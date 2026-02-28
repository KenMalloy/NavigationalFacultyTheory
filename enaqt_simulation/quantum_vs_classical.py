"""
Quantum vs Classical transport comparison.

Tests whether the coherent Hamiltonian contributes to transport efficiency
by comparing:

Comparison A:  Full quantum (H + bath + sink) vs classical (H=0, same bath
               Lindblad operators + sink) at physiological bath strength.

Comparison B:  Sweep Hamiltonian scaling factor alpha from 0 to 2, keeping
               bath operators fixed (derived from H at alpha=1).
               alpha=0  -> purely classical (no coherent dynamics)
               alpha=1  -> physiological (full Hamiltonian)
               alpha=2  -> double coherence

Uses the secular Redfield approach (mesolve with eigenstate-derived Lindblad
operators) validated against brmesolve.
"""

from __future__ import annotations

import argparse
import sys
import time

import numpy as np
from scipy.linalg import eigh

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    rad_ps_to_cm,
    KB_OVER_HBAR_PS_K,
)


# -----------------------------------------------------------------------
# Parameters (matching the task specification exactly)
# -----------------------------------------------------------------------

SITES = 8
COUPLING_CM = 60.0
DISORDER_CM = 25.0
SEED = 7
HELIX_RADIUS_NM = 2.0
HELIX_RISE_NM = 0.8
HELIX_TWIST_DEG = 27.7
DIPOLE_TILT_DEG = 20.0

BATH_STRENGTH_CM = 35.0    # physiological
CUTOFF_CM = 53.0
TEMPERATURE_K = 310.0

SINK_SITE = 7              # last site (0-indexed)
SINK_RATE_CM = 1.0
SOURCE_SITE = 0

T_MAX_PS = 50.0
N_TIME_POINTS = 500

N_ALPHA = 20                # number of alpha values for Comparison B


def derive_lindblad_operators(
    H_chromophore: np.ndarray,
    bath_strength_rad_ps: float,
    cutoff_rad_ps: float,
    kT_rad_ps: float,
    sink_site: int,
    sink_rate_ps_inv: float,
):
    """
    Derive the secular Redfield Lindblad operators from the full Hamiltonian.

    Returns (collapse_ops, eigvals, eigvecs) where collapse_ops is a list
    of QuTiP Qobj operators in the extended (N+1) Hilbert space.

    These operators encode the bath-induced transition rates and pure
    dephasing, derived from the eigenstates of H_chromophore.
    """
    import qutip

    N = H_chromophore.shape[0]
    N_total = N + 1  # +1 for the trap site

    # Diagonalize Hamiltonian
    eigvals, eigvecs = eigh(H_chromophore)

    # Drude-Lorentz spectral density
    def J_drude(omega):
        if omega <= 0:
            return 0.0
        return (2.0 * bath_strength_rad_ps * cutoff_rad_ps * omega
                / (omega ** 2 + cutoff_rad_ps ** 2))

    # Bose-Einstein distribution
    def n_bose(omega):
        if abs(omega) < 1e-12:
            return kT_rad_ps / (omega + 1e-30)  # high-T limit
        x = omega / kT_rad_ps
        if x > 500:
            return 0.0
        return 1.0 / (np.exp(x) - 1.0)

    collapse_ops = []

    # Transition operators between eigenstates
    for a in range(N):
        for b in range(a + 1, N):
            delta_E = eigvals[b] - eigvals[a]  # b has higher energy
            if delta_E < 1e-12:
                continue

            # Sum over baths (sites): each site j contributes independently
            gamma_factor = 0.0
            for j in range(N):
                gamma_factor += abs(eigvecs[j, a] * eigvecs[j, b]) ** 2

            if gamma_factor < 1e-15:
                continue

            j_val = J_drude(delta_E)
            n_th = n_bose(delta_E)

            # Downhill rate (b -> a, losing energy)
            rate_down = gamma_factor * j_val * (n_th + 1.0)
            # Uphill rate (a -> b, gaining energy)
            rate_up = gamma_factor * j_val * n_th

            if rate_down > 1e-15:
                # |a><b| in extended Hilbert space
                op_arr = np.zeros((N_total, N_total), dtype=complex)
                for site_i in range(N):
                    for site_j in range(N):
                        op_arr[site_i, site_j] += (
                            np.sqrt(rate_down) * eigvecs[site_i, a]
                            * np.conj(eigvecs[site_j, b])
                        )
                collapse_ops.append(qutip.Qobj(op_arr))

            if rate_up > 1e-15:
                # |b><a| in extended Hilbert space
                op_arr = np.zeros((N_total, N_total), dtype=complex)
                for site_i in range(N):
                    for site_j in range(N):
                        op_arr[site_i, site_j] += (
                            np.sqrt(rate_up) * eigvecs[site_i, b]
                            * np.conj(eigvecs[site_j, a])
                        )
                collapse_ops.append(qutip.Qobj(op_arr))

    # Pure dephasing operators
    S_zero = 4.0 * bath_strength_rad_ps * kT_rad_ps / cutoff_rad_ps

    for j in range(N):
        diag_elements = np.array([abs(eigvecs[j, a]) ** 2 for a in range(N)])
        if np.max(np.abs(diag_elements)) < 1e-15:
            continue

        op_eig = np.diag(diag_elements) * np.sqrt(S_zero)
        op_site = eigvecs @ op_eig @ eigvecs.conj().T

        op_ext = np.zeros((N_total, N_total), dtype=complex)
        op_ext[:N, :N] = op_site
        collapse_ops.append(qutip.Qobj(op_ext))

    # Sink collapse operator: |trap><sink_site|
    c_arr = np.zeros((N_total, N_total), dtype=float)
    c_arr[N, sink_site] = np.sqrt(sink_rate_ps_inv)
    collapse_ops.append(qutip.Qobj(c_arr))

    return collapse_ops, eigvals, eigvecs


def run_with_hamiltonian_scaling(
    H_chromophore: np.ndarray,
    alpha: float,
    collapse_ops: list,
    source_site: int,
    t_max: float,
    n_time_points: int,
) -> float:
    """
    Run mesolve with H_eff = alpha * H_chromophore (extended) and the
    pre-computed collapse operators.

    Returns transport efficiency (trap population at T_max).
    """
    import qutip

    N = H_chromophore.shape[0]
    N_total = N + 1

    # Build extended Hamiltonian with scaling
    H_ext = np.zeros((N_total, N_total), dtype=complex)
    H_ext[:N, :N] = alpha * H_chromophore
    H_qobj = qutip.Qobj(H_ext)

    # Initial state: excitation on source site
    psi0 = qutip.basis(N_total, source_site)

    # Time list
    tlist = np.linspace(0, t_max, n_time_points)

    # Run mesolve
    result = qutip.mesolve(H_qobj, psi0, tlist, c_ops=collapse_ops)

    # Transport efficiency = trap population at T_max
    rho_final = result.states[-1]
    efficiency = float(np.real(rho_final[N, N]))

    return efficiency


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantum vs Classical transport comparison"
    )
    parser.add_argument(
        "--sites", type=int, default=SITES,
        help=f"Number of chromophore sites (default: {SITES})"
    )
    args = parser.parse_args()

    sites = args.sites
    sink_site = sites - 1  # last site is the sink
    source_site = SOURCE_SITE

    print("=" * 72)
    print("QUANTUM vs CLASSICAL TRANSPORT COMPARISON")
    print("Does the coherent Hamiltonian help transport?")
    print("=" * 72)
    print()

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------

    sink_rate = cm_to_rad_ps(SINK_RATE_CM)
    cutoff_rad_ps = cm_to_rad_ps(CUTOFF_CM)
    kT_rad_ps = KB_OVER_HBAR_PS_K * TEMPERATURE_K
    bath_strength_rad_ps = cm_to_rad_ps(BATH_STRENGTH_CM)

    model = build_helix_model(
        sites=sites,
        coupling_cm=COUPLING_CM,
        disorder_cm=DISORDER_CM,
        seed=SEED,
        helix_radius_nm=HELIX_RADIUS_NM,
        helix_rise_nm=HELIX_RISE_NM,
        helix_twist_deg=HELIX_TWIST_DEG,
        dipole_tilt_deg=DIPOLE_TILT_DEG,
    )

    H = model.hamiltonian  # in rad/ps

    print("Parameters:")
    print(f"  sites                   : {sites}")
    print(f"  coupling_cm             : {COUPLING_CM}")
    print(f"  disorder_cm             : {DISORDER_CM}")
    print(f"  seed                    : {SEED}")
    print(f"  bath_strength_cm        : {BATH_STRENGTH_CM}")
    print(f"  cutoff_cm               : {CUTOFF_CM}")
    print(f"  temperature_K           : {TEMPERATURE_K}")
    print(f"  kT (rad/ps)             : {kT_rad_ps:.6f}")
    print(f"  sink_site               : {sink_site}")
    print(f"  sink_rate_cm            : {SINK_RATE_CM}")
    print(f"  sink_rate (ps^-1)       : {sink_rate:.6f}")
    print(f"  source_site             : {source_site}")
    print(f"  T_max (ps)              : {T_MAX_PS}")
    print(f"  n_time_points           : {N_TIME_POINTS}")
    print(f"  model                   : {model.label}")
    print(f"  nn_coupling_median_cm   : {model.nearest_neighbor_median_cm:.4f}")
    print()

    # Eigenstate analysis
    eigvals, eigvecs = eigh(H)
    eigvals_cm = rad_ps_to_cm(eigvals)
    gaps = np.diff(eigvals)
    gaps_cm = rad_ps_to_cm(gaps)

    print("Eigenstates of H (used to derive bath operators):")
    for i, e_cm in enumerate(eigvals_cm):
        print(f"  |{i}> : {e_cm:10.4f} cm^-1  ({eigvals[i]:10.6f} rad/ps)")
    print()
    print("Eigenstate gaps:")
    for i, g_cm in enumerate(gaps_cm):
        print(f"  |{i}> -> |{i+1}> : {g_cm:10.4f} cm^-1  ({gaps[i]:10.6f} rad/ps)")
    print()

    # ---------------------------------------------------------------
    # Derive Lindblad operators at alpha=1 (full H)
    # These are FIXED for all runs -- they encode the bath-induced
    # hopping rates derived from the true eigenstates.
    # ---------------------------------------------------------------

    print("Deriving Lindblad operators from full Hamiltonian (alpha=1)...")
    t0 = time.time()
    collapse_ops, _, _ = derive_lindblad_operators(
        H_chromophore=H,
        bath_strength_rad_ps=bath_strength_rad_ps,
        cutoff_rad_ps=cutoff_rad_ps,
        kT_rad_ps=kT_rad_ps,
        sink_site=sink_site,
        sink_rate_ps_inv=sink_rate,
    )
    dt = time.time() - t0
    print(f"  Number of collapse operators: {len(collapse_ops)}")
    print(f"  Time to derive: {dt:.3f} s")
    print()

    # ===============================================================
    # COMPARISON A: Quantum vs Classical at physiological bath
    # ===============================================================

    print("=" * 72)
    print("COMPARISON A: Quantum vs Classical at lambda = 35 cm^-1")
    print("=" * 72)
    print()
    print("  'Quantum'  = Full H + bath Lindblad + sink  (alpha = 1)")
    print("  'Classical' = H = 0 + SAME bath Lindblad + sink  (alpha = 0)")
    print("  Bath operators are identical in both cases (derived from full H).")
    print("  The only difference is whether coherent dynamics (-i[H, rho]) is present.")
    print()

    # Quantum (alpha=1)
    print("Running quantum (alpha=1)...")
    t0 = time.time()
    eff_quantum = run_with_hamiltonian_scaling(
        H_chromophore=H,
        alpha=1.0,
        collapse_ops=collapse_ops,
        source_site=source_site,
        t_max=T_MAX_PS,
        n_time_points=N_TIME_POINTS,
    )
    dt_q = time.time() - t0
    print(f"  Quantum efficiency:  {eff_quantum:.6f}  ({dt_q:.2f} s)")

    # Classical (alpha=0)
    print("Running classical (alpha=0)...")
    t0 = time.time()
    eff_classical = run_with_hamiltonian_scaling(
        H_chromophore=H,
        alpha=0.0,
        collapse_ops=collapse_ops,
        source_site=source_site,
        t_max=T_MAX_PS,
        n_time_points=N_TIME_POINTS,
    )
    dt_c = time.time() - t0
    print(f"  Classical efficiency: {eff_classical:.6f}  ({dt_c:.2f} s)")

    quantum_advantage = eff_quantum - eff_classical
    if eff_classical > 1e-10:
        relative_advantage = (quantum_advantage / eff_classical) * 100.0
    else:
        relative_advantage = float("inf")

    print()
    print(f"  Quantum advantage    = {quantum_advantage:+.6f}")
    print(f"  Relative advantage   = {relative_advantage:+.2f}%")
    print()

    # ===============================================================
    # COMPARISON B: Hamiltonian scaling sweep (alpha = 0 to 2)
    # ===============================================================

    print("=" * 72)
    print("COMPARISON B: Hamiltonian scaling sweep (alpha = 0 to 2)")
    print("=" * 72)
    print()
    print("  H_eff = alpha * H_full")
    print("  Bath operators FIXED (derived from H at alpha=1)")
    print("  alpha=0: purely classical (no coherent dynamics)")
    print("  alpha=1: physiological (full Hamiltonian)")
    print("  alpha=2: double coherence")
    print()

    alphas = np.linspace(0.0, 2.0, N_ALPHA)
    efficiencies = []

    print(f"{'idx':>4} {'alpha':>8} {'efficiency':>12} {'time_s':>8}")
    print("-" * 36)

    for idx, alpha in enumerate(alphas):
        t0 = time.time()
        eff = run_with_hamiltonian_scaling(
            H_chromophore=H,
            alpha=alpha,
            collapse_ops=collapse_ops,
            source_site=source_site,
            t_max=T_MAX_PS,
            n_time_points=N_TIME_POINTS,
        )
        dt = time.time() - t0
        efficiencies.append(eff)
        print(f"{idx+1:4d} {alpha:8.4f} {eff:12.6f} {dt:8.2f}")

    eff_arr = np.array(efficiencies)

    # ===============================================================
    # RESULTS SUMMARY
    # ===============================================================

    print()
    print("=" * 72)
    print("RESULTS SUMMARY")
    print("=" * 72)
    print()

    # Key values
    eff_alpha_0 = eff_arr[0]   # alpha=0 (classical)
    # Find the index closest to alpha=1
    idx_alpha_1 = int(np.argmin(np.abs(alphas - 1.0)))
    eff_alpha_1 = eff_arr[idx_alpha_1]
    eff_alpha_max = float(np.max(eff_arr))
    alpha_at_max = alphas[int(np.argmax(eff_arr))]
    eff_alpha_2 = eff_arr[-1]  # alpha=2 (double coherence)

    print(f"  Classical efficiency (alpha=0):   {eff_alpha_0:.6f}")
    print(f"  Quantum efficiency (alpha=1):     {eff_alpha_1:.6f}")
    print(f"  Double-coherence (alpha=2):       {eff_alpha_2:.6f}")
    print(f"  Peak efficiency:                  {eff_alpha_max:.6f}  (at alpha={alpha_at_max:.4f})")
    print()

    quantum_advantage_final = eff_alpha_1 - eff_alpha_0
    if eff_alpha_0 > 1e-10:
        relative_adv_final = (quantum_advantage_final / eff_alpha_0) * 100.0
    else:
        relative_adv_final = float("inf")

    print(f"  QUANTUM ADVANTAGE = efficiency(alpha=1) - efficiency(alpha=0)")
    print(f"                    = {eff_alpha_1:.6f} - {eff_alpha_0:.6f}")
    print(f"                    = {quantum_advantage_final:+.6f}")
    print(f"                    = {relative_adv_final:+.2f}% relative to classical")
    print()

    # Efficiency range across alpha sweep
    eff_range = float(np.max(eff_arr) - np.min(eff_arr))
    eff_mean = float(np.mean(eff_arr))
    eff_cv = float(np.std(eff_arr) / eff_mean) * 100 if eff_mean > 1e-10 else 0.0

    print(f"  Efficiency range across sweep:    {eff_range:.6f}")
    print(f"  Efficiency mean:                  {eff_mean:.6f}")
    print(f"  Coefficient of variation:         {eff_cv:.4f}%")
    print()

    # ---------------------------------------------------------------
    # VERDICT
    # ---------------------------------------------------------------

    print("=" * 72)
    print("VERDICT")
    print("=" * 72)
    print()

    # Determine if quantum helps
    SIGNIFICANT_THRESHOLD = 0.02  # 2 percentage points
    MODERATE_THRESHOLD = 0.005    # 0.5 percentage points

    if quantum_advantage_final > SIGNIFICANT_THRESHOLD:
        verdict = "QUANTUM COHERENCE SIGNIFICANTLY HELPS TRANSPORT"
        detail = (
            f"The Hamiltonian contributes +{quantum_advantage_final:.4f} "
            f"({relative_adv_final:+.1f}%) to transport efficiency. "
            f"Removing coherent dynamics (alpha=0) drops efficiency from "
            f"{eff_alpha_1:.4f} to {eff_alpha_0:.4f}. "
            f"This is a large effect -- quantum coherence robustly enhances "
            f"transport beyond what the bath alone can achieve."
        )
    elif quantum_advantage_final > MODERATE_THRESHOLD:
        verdict = "QUANTUM COHERENCE MODERATELY HELPS TRANSPORT"
        detail = (
            f"The Hamiltonian contributes +{quantum_advantage_final:.4f} "
            f"({relative_adv_final:+.1f}%) to transport efficiency. "
            f"This is a modest but real quantum advantage."
        )
    elif quantum_advantage_final > -MODERATE_THRESHOLD:
        verdict = "QUANTUM COHERENCE HAS NEGLIGIBLE EFFECT ON TRANSPORT"
        detail = (
            f"The difference between quantum ({eff_alpha_1:.4f}) and "
            f"classical ({eff_alpha_0:.4f}) is only {quantum_advantage_final:+.4f} "
            f"({relative_adv_final:+.1f}%). "
            f"The bath-induced hopping alone accounts for essentially all "
            f"of the transport. The Hamiltonian is neither helping nor hurting."
        )
    elif quantum_advantage_final > -SIGNIFICANT_THRESHOLD:
        verdict = "QUANTUM COHERENCE MODERATELY HINDERS TRANSPORT"
        detail = (
            f"Adding the Hamiltonian slightly reduces efficiency by "
            f"{abs(quantum_advantage_final):.4f} ({relative_adv_final:+.1f}%). "
            f"Coherent dynamics may be creating interference that hinders "
            f"bath-driven transport."
        )
    else:
        verdict = "QUANTUM COHERENCE SIGNIFICANTLY HINDERS TRANSPORT"
        detail = (
            f"Adding the Hamiltonian reduces efficiency by "
            f"{abs(quantum_advantage_final):.4f} ({relative_adv_final:+.1f}%). "
            f"Coherent quantum dynamics actively interfere with the "
            f"classical hopping pathway."
        )

    print(f"  {verdict}")
    print()
    print(f"  {detail}")
    print()

    # Additional interpretation
    print("  Interpretation for the ENAQT thesis:")
    if quantum_advantage_final > MODERATE_THRESHOLD:
        print(f"    - Classical bath-driven transport alone gives {eff_alpha_0:.4f}")
        print(f"    - Adding the Hamiltonian boosts this to {eff_alpha_1:.4f}")
        print(f"    - The ~62% efficiency seen in Bloch-Redfield sweep is NOT")
        print(f"      purely classical -- quantum coherence contributes")
        print(f"      {quantum_advantage_final:.4f} of it.")
        print(f"    - Level B (quantum coherence enhances transport) is SUPPORTED.")
    elif quantum_advantage_final > -MODERATE_THRESHOLD:
        print(f"    - Classical bath-driven transport gives {eff_alpha_0:.4f}")
        print(f"    - Quantum transport gives {eff_alpha_1:.4f}")
        print(f"    - The bath alone reproduces the full transport efficiency.")
        print(f"    - The Hamiltonian is essentially irrelevant at this bath strength.")
        print(f"    - Level B (quantum coherence enhances transport) is CHALLENGED.")
        print(f"    - The flat efficiency curve is explained: the bath dominates")
        print(f"      and coherence is washed out at lambda=35 cm^-1.")
    else:
        print(f"    - Classical bath-driven transport gives {eff_alpha_0:.4f}")
        print(f"    - Adding the Hamiltonian REDUCES this to {eff_alpha_1:.4f}")
        print(f"    - Quantum coherence actively interferes with transport.")
        print(f"    - Level B is CONTRADICTED at this bath strength.")

    print()

    # Monotonicity check
    is_monotone_decreasing = all(
        eff_arr[i] >= eff_arr[i + 1] - 1e-6 for i in range(len(eff_arr) - 1)
    )
    is_monotone_increasing = all(
        eff_arr[i] <= eff_arr[i + 1] + 1e-6 for i in range(len(eff_arr) - 1)
    )

    if is_monotone_decreasing:
        print("  Alpha dependence: MONOTONICALLY DECREASING")
        print("    More coherence -> less transport. Bath is optimal alone.")
    elif is_monotone_increasing:
        print("  Alpha dependence: MONOTONICALLY INCREASING")
        print("    More coherence -> more transport. Coherence is purely beneficial.")
    else:
        # Check for a peak
        peak_idx = int(np.argmax(eff_arr))
        if 0 < peak_idx < len(eff_arr) - 1:
            print(f"  Alpha dependence: NON-MONOTONE (peak at alpha={alphas[peak_idx]:.4f})")
            print(f"    Transport peaks at intermediate coherence strength.")
            print(f"    This is the hallmark of ENAQT: too little or too much")
            print(f"    coherence is suboptimal.")
        else:
            print(f"  Alpha dependence: NON-MONOTONE (complex pattern)")

    print()
    print("=" * 72)
    print("END OF QUANTUM vs CLASSICAL COMPARISON")
    print("=" * 72)


if __name__ == "__main__":
    main()
