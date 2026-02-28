"""
Phase 2b ENAQT transport via Bloch-Redfield master equation.

Uses QuTiP's brmesolve with a Drude-Lorentz spectral density to derive
dephasing and relaxation rates from the ACTUAL bath spectral density
evaluated at the ACTUAL eigenstate energy gaps.  This is more physical
than the phenomenological Lindblad (QSW) operators used in phase2_transport.py.

Key differences from the phenomenological approach:
  - Dissipation rates are derived from J(ω) at the true eigenstate gaps
  - Detailed balance is automatically respected
  - Both dephasing and relaxation are captured self-consistently
  - The effective dephasing rate depends on the bath strength λ (reorganization
    energy) rather than being set by hand

The sweep parameter is the bath reorganization energy λ (bath_strength_cm).
As λ increases, both dephasing and relaxation rates increase because
J(ω) ∝ λ.  We look for the ENAQT peak: transport efficiency should be
maximized at some intermediate λ.

Architecture:
  - 8 chromophore sites (from helix geometry) + 1 auxiliary trap site
  - The Hamiltonian acts on the 8+1 = 9-dimensional Hilbert space, with
    no coupling between chromophore sites and the trap in H
  - Each chromophore site j couples to its own independent bath via the
    diagonal operator |j><j| (pure dephasing coupling in the site basis)
  - An irreversible sink on the last chromophore site is modeled as a
    Lindblad collapse operator: C_sink = sqrt(Γ_sink) |trap><last_site|
  - Transport efficiency = population in the trap site at t = T_max
"""

from __future__ import annotations

import argparse
import sys
import time
from math import pi
from pathlib import Path

import numpy as np

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    rad_ps_to_cm,
    reference_gap_ps_inv,
    derive_kappa,
    KB_OVER_HBAR_PS_K,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 2b: ENAQT via Bloch-Redfield master equation."
    )
    # Helix geometry
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--coupling-cm", type=float, default=60.0)
    parser.add_argument("--disorder-cm", type=float, default=25.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--helix-radius-nm", type=float, default=2.0)
    parser.add_argument("--helix-rise-nm", type=float, default=0.8)
    parser.add_argument("--helix-twist-deg", type=float, default=27.7)
    parser.add_argument("--dipole-tilt-deg", type=float, default=20.0)
    # Bath
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    # Sweep: bath reorganization energy λ
    parser.add_argument("--lambda-min-cm", type=float, default=1.0,
                        help="Minimum bath strength (cm^-1)")
    parser.add_argument("--lambda-max-cm", type=float, default=500.0,
                        help="Maximum bath strength (cm^-1)")
    parser.add_argument("--lambda-count", type=int, default=30,
                        help="Number of sweep points")
    # Sink / source
    parser.add_argument("--sink-site", type=int, default=-1,
                        help="Sink site index (-1 = last site)")
    parser.add_argument("--sink-rate-cm", type=float, default=1.0,
                        help="Sink trapping rate in cm^-1")
    parser.add_argument("--source-site", type=int, default=0,
                        help="Initial excitation site")
    # Time evolution
    parser.add_argument("--t-max-ps", type=float, default=50.0,
                        help="Maximum simulation time in ps")
    parser.add_argument("--n-time-points", type=int, default=500,
                        help="Number of time points")
    # Method selection
    parser.add_argument("--method", type=str, default="brmesolve",
                        choices=["brmesolve", "secular-redfield"],
                        help="Solver method")
    # Output
    parser.add_argument("--csv-out", type=Path, default=None)
    return parser.parse_args()


# -----------------------------------------------------------------------
# brmesolve-based solver (QuTiP native Bloch-Redfield)
# -----------------------------------------------------------------------

def run_brmesolve(
    H_chromophore: np.ndarray,
    source_site: int,
    sink_site: int,
    sink_rate_ps_inv: float,
    bath_strength_rad_ps: float,
    cutoff_rad_ps: float,
    kT_rad_ps: float,
    t_max: float,
    n_time_points: int,
) -> float:
    """
    Run brmesolve for a single bath-strength value and return the
    transport efficiency.

    The Hilbert space is extended by one trap site (index N) to capture
    population irreversibly removed from the chromophore network.
    """
    import qutip
    from qutip.core.environment import DrudeLorentzEnvironment

    N = H_chromophore.shape[0]   # number of chromophore sites
    N_total = N + 1               # +1 for the trap site

    # Build extended Hamiltonian (trap site has zero energy, no coupling)
    H_ext = np.zeros((N_total, N_total), dtype=complex)
    H_ext[:N, :N] = H_chromophore
    H_qobj = qutip.Qobj(H_ext)

    # Initial state: excitation on source site
    psi0 = qutip.basis(N_total, source_site)

    # Time list
    tlist = np.linspace(0, t_max, n_time_points)

    # Bath coupling: each chromophore site couples to its own bath
    # via diagonal operator |j><j| (pure dephasing in site basis)
    # DrudeLorentzEnvironment: T = kT (energy units), lam = λ, gamma = γ_c
    env = DrudeLorentzEnvironment(
        T=kT_rad_ps,
        lam=bath_strength_rad_ps,
        gamma=cutoff_rad_ps,
    )

    a_ops = []
    for j in range(N):
        proj = np.zeros((N_total, N_total), dtype=float)
        proj[j, j] = 1.0
        a_ops.append((qutip.Qobj(proj), env))

    # Sink collapse operator: transfers population from sink_site to trap
    # C = sqrt(Gamma) |trap><sink_site|
    c_arr = np.zeros((N_total, N_total), dtype=float)
    c_arr[N, sink_site] = np.sqrt(sink_rate_ps_inv)
    c_sink = qutip.Qobj(c_arr)

    # Run Bloch-Redfield solver
    result = qutip.brmesolve(
        H_qobj,
        psi0,
        tlist,
        a_ops=a_ops,
        c_ops=[c_sink],
    )

    # Transport efficiency = population in the trap site at T_max
    rho_final = result.states[-1]
    efficiency = float(np.real(rho_final[N, N]))

    return efficiency


# -----------------------------------------------------------------------
# Secular Redfield solver (manual, using mesolve)
# -----------------------------------------------------------------------

def run_secular_redfield(
    H_chromophore: np.ndarray,
    source_site: int,
    sink_site: int,
    sink_rate_ps_inv: float,
    bath_strength_rad_ps: float,
    cutoff_rad_ps: float,
    kT_rad_ps: float,
    t_max: float,
    n_time_points: int,
) -> float:
    """
    Secular Redfield approach using mesolve:

    1. Diagonalize H to get eigenstates |a> with energies E_a
    2. For each pair (a,b) with E_a > E_b, compute:
       - Drude-Lorentz spectral density J(ω) at ω = E_a - E_b
       - Downhill rate: Γ_ab = Σ_j |<a|j><j|b>|² * J(ΔE) * (n_th(ΔE) + 1)
       - Uphill rate:   Γ_ba = Σ_j |<a|j><j|b>|² * J(ΔE) * n_th(ΔE)
       - Lindblad operators for these transitions
    3. Also add pure dephasing terms from J(0) limit
    4. Use mesolve with these collapse operators + sink
    """
    import qutip
    from scipy.linalg import eigh

    N = H_chromophore.shape[0]
    N_total = N + 1  # +1 for the trap site

    # Diagonalize Hamiltonian
    eigvals, eigvecs = eigh(H_chromophore)
    # eigvecs[:, a] is the a-th eigenstate in the site basis

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

    # Build extended Hamiltonian
    H_ext = np.zeros((N_total, N_total), dtype=complex)
    H_ext[:N, :N] = H_chromophore
    H_qobj = qutip.Qobj(H_ext)

    # Compute overlap factors: for site-diagonal coupling |j><j|,
    # the matrix element <a|j><j|b> = eigvecs[j, a]* eigvecs[j, b]
    # The total coupling strength for transition a<->b summed over baths:
    # gamma_factor(a,b) = Σ_j |<a|j><j|b>|² = Σ_j |V_ja|² |V_jb|²
    # where V_ja = eigvecs[j, a]

    collapse_ops = []

    for a in range(N):
        for b in range(a + 1, N):
            delta_E = eigvals[b] - eigvals[a]  # b has higher energy
            if delta_E < 1e-12:
                continue

            # Sum over baths (sites): each site j contributes independently
            # |<a|P_j|b>|^2 = |V_ja * V_jb|^2
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

    # Pure dephasing from the secular Redfield tensor.
    #
    # In the secular approximation, diagonal coupling operators |j><j|
    # produce "elastic" scattering that dephases eigenstate coherences
    # without causing population transfer.  The pure dephasing rate for
    # coherence ρ_{ab} (a ≠ b) is:
    #
    #   γ_pure(a,b) = Σ_j (<a|P_j|a> - <b|P_j|b>)^2 * S(0)
    #
    # where S(0) = lim_{ω→0} [J(ω) * coth(ω/(2kT))]
    #            = 2λkT / γ_c   (Drude-Lorentz at high T)
    #
    # This is implemented via Lindblad operators of the form:
    #   L_ab = sqrt(γ_pure(a,b)) * |a><a| for each pair
    # But that would cause double-counting.  Instead, we add a single
    # dephasing operator for each eigenstate |a> that captures the
    # elastic contribution from each bath:
    #
    #   L_j = sqrt(S(0)) * Σ_a <a|P_j|a> |a><a|
    #
    # This gives the correct dephasing without population transfer.
    # (The resulting dephasing rate for ρ_{ab} is
    #   Σ_j S(0) * (<a|P_j|a> - <b|P_j|b>)^2 as required.)

    # S(0) for Drude-Lorentz: lim_{ω→0} 2λγ_cω/(ω²+γ_c²) * coth(ω/(2kT))
    # = 2λγ_c * (2kT) / γ_c² = 4λkT / γ_c  [using J(ω)→2λω/γ_c, coth→2kT/ω]
    # Actually: S(ω) = J(ω)*(1+2*n_bose(ω)), and for ω→0:
    #   J(ω) → 2λω/γ_c, n_bose(ω) → kT/ω
    #   S(0) = lim 2λω/γ_c * (1 + 2kT/ω) = lim 2λω/γ_c + 4λkT/γ_c
    #        = 4λkT/γ_c
    S_zero = 4.0 * bath_strength_rad_ps * kT_rad_ps / cutoff_rad_ps

    for j in range(N):
        # Diagonal matrix elements <a|P_j|a> = |eigvecs[j,a]|^2
        diag_elements = np.array([abs(eigvecs[j, a]) ** 2 for a in range(N)])

        # Check if this bath contributes any dephasing
        if np.max(np.abs(diag_elements)) < 1e-15:
            continue

        # L_j = sqrt(S(0)) * Σ_a <a|P_j|a> |a><a|
        # In the site basis: L_j = sqrt(S(0)) * Σ_a <a|P_j|a> |a><a|
        # = sqrt(S(0)) * U * diag(<a|P_j|a>) * U^†
        op_eig = np.diag(diag_elements) * np.sqrt(S_zero)
        # Transform back to site basis
        op_site = eigvecs @ op_eig @ eigvecs.conj().T

        # Embed in extended Hilbert space
        op_ext = np.zeros((N_total, N_total), dtype=complex)
        op_ext[:N, :N] = op_site
        collapse_ops.append(qutip.Qobj(op_ext))

    # Sink collapse operator: |trap><sink_site|
    c_arr = np.zeros((N_total, N_total), dtype=float)
    c_arr[N, sink_site] = np.sqrt(sink_rate_ps_inv)
    collapse_ops.append(qutip.Qobj(c_arr))

    # Initial state
    psi0 = qutip.basis(N_total, source_site)

    # Time list
    tlist = np.linspace(0, t_max, n_time_points)

    # Run mesolve
    result = qutip.mesolve(H_qobj, psi0, tlist, c_ops=collapse_ops)

    # Transport efficiency = trap population at T_max
    rho_final = result.states[-1]
    efficiency = float(np.real(rho_final[N, N]))

    return efficiency


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # Resolve sink site
    sink_site = args.sink_site
    if sink_site < 0:
        sink_site = args.sites + sink_site

    sink_rate = cm_to_rad_ps(args.sink_rate_cm)
    cutoff_rad_ps = cm_to_rad_ps(args.cutoff_cm)
    kT_rad_ps = KB_OVER_HBAR_PS_K * args.temperature_k

    # 1. Build helix model
    model = build_helix_model(
        sites=args.sites,
        coupling_cm=args.coupling_cm,
        disorder_cm=args.disorder_cm,
        seed=args.seed,
        helix_radius_nm=args.helix_radius_nm,
        helix_rise_nm=args.helix_rise_nm,
        helix_twist_deg=args.helix_twist_deg,
        dipole_tilt_deg=args.dipole_tilt_deg,
    )

    H = model.hamiltonian  # in rad/ps
    V = cm_to_rad_ps(model.nearest_neighbor_median_cm)

    # Reference gap for comparison with phenomenological approach
    omega_ref = reference_gap_ps_inv(H)

    # Choose solver
    use_brmesolve = (args.method == "brmesolve")
    method_label = "brmesolve (QuTiP native Bloch-Redfield)" if use_brmesolve else "secular Redfield (mesolve with derived rates)"

    print("ENAQT Phase 2b: Bloch-Redfield Transport Simulation")
    print("=" * 70)
    print(f"method                    : {method_label}")
    print(f"model_label               : {model.label}")
    print(f"sites                     : {args.sites}")
    print(f"coupling_cm               : {args.coupling_cm}")
    print(f"disorder_cm               : {args.disorder_cm}")
    print(f"seed                      : {args.seed}")
    print(f"nn_coupling_median_cm     : {model.nearest_neighbor_median_cm:.4f}")
    print(f"V (nn coupling, rad/ps)   : {V:.6f}")
    print(f"reference_gap (rad/ps)    : {omega_ref:.6f}")
    print(f"cutoff_cm                 : {args.cutoff_cm}")
    print(f"cutoff (rad/ps)           : {cutoff_rad_ps:.6f}")
    print(f"temperature_K             : {args.temperature_k}")
    print(f"kT (rad/ps)              : {kT_rad_ps:.6f}")
    print(f"source_site               : {args.source_site}")
    print(f"sink_site                 : {sink_site}")
    print(f"sink_rate_cm              : {args.sink_rate_cm}")
    print(f"sink_rate (ps^-1)         : {sink_rate:.6f}")
    print(f"t_max (ps)                : {args.t_max_ps}")
    print(f"n_time_points             : {args.n_time_points}")
    print(f"bath strength sweep       : {args.lambda_min_cm} -- {args.lambda_max_cm} cm^-1 ({args.lambda_count} points)")
    print()

    # Eigenstate analysis
    from scipy.linalg import eigh
    eigvals, eigvecs = eigh(H)
    eigvals_cm = rad_ps_to_cm(eigvals)
    gaps = np.diff(eigvals)
    gaps_cm = rad_ps_to_cm(gaps)

    print("Eigenstate energies (cm^-1):")
    for i, e_cm in enumerate(eigvals_cm):
        print(f"  |{i}> : {e_cm:10.4f} cm^-1  ({eigvals[i]:10.6f} rad/ps)")
    print()
    print("Eigenstate gaps (cm^-1):")
    for i, g_cm in enumerate(gaps_cm):
        print(f"  |{i}> -> |{i+1}> : {g_cm:10.4f} cm^-1  ({gaps[i]:10.6f} rad/ps)")
    print()

    # 2. Sweep bath strength
    lambdas_cm = np.logspace(
        np.log10(args.lambda_min_cm),
        np.log10(args.lambda_max_cm),
        args.lambda_count,
    )

    efficiencies = []
    kappa_effectives = []

    solver_fn = run_brmesolve if use_brmesolve else run_secular_redfield

    print(f"{'idx':>4} {'lambda_cm':>10} {'lambda_rad_ps':>14} "
          f"{'efficiency':>12} {'kappa_eff':>12} {'gamma/kappa':>12} "
          f"{'time_s':>8}")
    print("-" * 85)

    for idx, lam_cm in enumerate(lambdas_cm):
        lam_rad_ps = cm_to_rad_ps(lam_cm)

        t0 = time.time()
        try:
            eff = solver_fn(
                H_chromophore=H,
                source_site=args.source_site,
                sink_site=sink_site,
                sink_rate_ps_inv=sink_rate,
                bath_strength_rad_ps=lam_rad_ps,
                cutoff_rad_ps=cutoff_rad_ps,
                kT_rad_ps=kT_rad_ps,
                t_max=args.t_max_ps,
                n_time_points=args.n_time_points,
            )
        except Exception as e:
            print(f"  [{idx+1:3d}/{args.lambda_count}] lambda={lam_cm:.2f} cm^-1  "
                  f"FAILED: {e}")
            if use_brmesolve:
                print("  Falling back to secular Redfield for this point...")
                try:
                    eff = run_secular_redfield(
                        H_chromophore=H,
                        source_site=args.source_site,
                        sink_site=sink_site,
                        sink_rate_ps_inv=sink_rate,
                        bath_strength_rad_ps=lam_rad_ps,
                        cutoff_rad_ps=cutoff_rad_ps,
                        kT_rad_ps=kT_rad_ps,
                        t_max=args.t_max_ps,
                        n_time_points=args.n_time_points,
                    )
                except Exception as e2:
                    print(f"    Fallback also failed: {e2}")
                    eff = 0.0
            else:
                eff = 0.0

        elapsed = time.time() - t0

        # Compute effective kappa for comparison with Phase 2
        # kappa_eff = derive_kappa at this bath strength
        kappa_eff = derive_kappa(
            omega_ref=omega_ref,
            bath_strength_cm=lam_cm,
            cutoff_cm=args.cutoff_cm,
            temperature_k=args.temperature_k,
        )
        gamma_over_kappa = V / kappa_eff if kappa_eff > 1e-15 else float("inf")

        efficiencies.append(eff)
        kappa_effectives.append(kappa_eff)

        print(f"{idx+1:4d} {lam_cm:10.2f} {lam_rad_ps:14.6f} "
              f"{eff:12.6f} {kappa_eff:12.6f} {gamma_over_kappa:12.4f} "
              f"{elapsed:8.2f}")

    # 3. Results table
    print()
    print("=" * 85)
    print("RESULTS TABLE")
    print("=" * 85)
    header = (f"{'lambda_cm':>10} {'kappa_eff':>12} {'gamma/kappa':>12} "
              f"{'efficiency':>12}")
    print(header)
    print("-" * len(header))
    for i, lam_cm in enumerate(lambdas_cm):
        gk = V / kappa_effectives[i] if kappa_effectives[i] > 1e-15 else float("inf")
        print(f"{lam_cm:10.4f} {kappa_effectives[i]:12.6e} {gk:12.4f} "
              f"{efficiencies[i]:12.6f}")

    # 4. Summary
    print()
    print("=" * 85)
    print("SUMMARY")
    print("=" * 85)

    eff_arr = np.array(efficiencies)
    max_eff = float(np.max(eff_arr))
    max_idx = int(np.argmax(eff_arr))
    max_lam = lambdas_cm[max_idx]
    max_kappa = kappa_effectives[max_idx]
    max_gk = V / max_kappa if max_kappa > 1e-15 else float("inf")

    print(f"peak efficiency           : {max_eff:.6f}")
    print(f"  at lambda               : {max_lam:.4f} cm^-1")
    print(f"  at kappa_eff            : {max_kappa:.6e} ps^-1")
    print(f"  at gamma/kappa          : {max_gk:.4f}")
    print()

    # Efficiency at physiological bath strength (35 cm^-1)
    phys_lam = 35.0
    # Find nearest sweep point
    phys_idx = int(np.argmin(np.abs(lambdas_cm - phys_lam)))
    phys_eff = efficiencies[phys_idx]
    phys_kappa = kappa_effectives[phys_idx]
    phys_gk = V / phys_kappa if phys_kappa > 1e-15 else float("inf")

    print(f"physiological lambda      : {phys_lam:.1f} cm^-1")
    print(f"  nearest sweep point     : {lambdas_cm[phys_idx]:.4f} cm^-1")
    print(f"  efficiency              : {phys_eff:.6f}")
    print(f"  kappa_eff               : {phys_kappa:.6e} ps^-1")
    print(f"  gamma/kappa             : {phys_gk:.4f}")
    print()

    # Compare with Phase 2 phenomenological result
    kappa_phys_phenom = derive_kappa(
        omega_ref=omega_ref,
        bath_strength_cm=35.0,
        cutoff_cm=args.cutoff_cm,
        temperature_k=args.temperature_k,
    )
    gk_phys_phenom = V / kappa_phys_phenom
    print(f"Phase 2 phenomenological comparison:")
    print(f"  kappa_phys (phenom)     : {kappa_phys_phenom:.6e} ps^-1")
    print(f"  gamma/kappa (phenom)    : {gk_phys_phenom:.4f}")
    print(f"  (Phase 2 found ENAQT peak at gamma/kappa ~ 41)")
    print()

    # Endpoints
    eff_low_lam = efficiencies[0]
    eff_high_lam = efficiencies[-1]
    print(f"efficiency at lambda_min  : {eff_low_lam:.6f} (lambda={lambdas_cm[0]:.2f} cm^-1, weak bath)")
    print(f"efficiency at lambda_max  : {eff_high_lam:.6f} (lambda={lambdas_cm[-1]:.2f} cm^-1, strong bath)")
    print()

    # ENAQT detection
    is_at_low_end = max_idx <= 2
    is_at_high_end = max_idx >= args.lambda_count - 3
    THRESHOLD = 0.005

    peak_adv_over_weak = max_eff - eff_low_lam
    peak_adv_over_strong = max_eff - eff_high_lam

    # Local maxima detection
    local_max_indices = []
    for k in range(1, len(eff_arr) - 1):
        if eff_arr[k] > eff_arr[k - 1] and eff_arr[k] > eff_arr[k + 1]:
            local_max_indices.append(k)

    if (
        not is_at_low_end
        and not is_at_high_end
        and peak_adv_over_weak > THRESHOLD
        and peak_adv_over_strong > THRESHOLD
    ):
        verdict = (
            f"ENAQT DETECTED (Bloch-Redfield): Transport efficiency peaks at "
            f"lambda = {max_lam:.2f} cm^-1 (gamma/kappa = {max_gk:.4f}), "
            f"with efficiency = {max_eff:.4f}. "
            f"This exceeds both the weak-bath limit ({eff_low_lam:.4f}) "
            f"and the strong-bath limit ({eff_high_lam:.4f}). "
            f"Peak advantage: +{peak_adv_over_weak:.4f} over weak bath, "
            f"+{peak_adv_over_strong:.4f} over strong bath."
        )
    elif local_max_indices:
        best_local = max(local_max_indices, key=lambda k: eff_arr[k])
        local_eff = eff_arr[best_local]
        local_lam = lambdas_cm[best_local]
        local_gk = V / kappa_effectives[best_local] if kappa_effectives[best_local] > 1e-15 else float("inf")
        left_min = float(np.min(eff_arr[:best_local + 1]))
        right_min = float(np.min(eff_arr[best_local:]))
        local_adv = min(local_eff - left_min, local_eff - right_min)
        if local_adv > THRESHOLD:
            verdict = (
                f"ENAQT DETECTED (local peak): Transport efficiency shows a local "
                f"maximum at lambda = {local_lam:.2f} cm^-1 (gamma/kappa = {local_gk:.4f}), "
                f"efficiency = {local_eff:.4f}, with local advantage {local_adv:.4f}."
            )
        else:
            verdict = (
                f"MARGINAL ENAQT: local peak at lambda = {local_lam:.2f} cm^-1 "
                f"(efficiency = {local_eff:.4f}), but advantage ({local_adv:.4f}) "
                f"below threshold {THRESHOLD}."
            )
    elif is_at_low_end:
        verdict = (
            f"NO ENAQT: efficiency highest at weak bath coupling "
            f"(lambda = {max_lam:.2f} cm^-1). Coherent transport dominates."
        )
    elif is_at_high_end:
        verdict = (
            f"NO ENAQT: efficiency highest at strong bath coupling "
            f"(lambda = {max_lam:.2f} cm^-1). Classical transport dominates."
        )
    else:
        verdict = (
            f"PLATEAU: efficiency peak at lambda = {max_lam:.2f} cm^-1 "
            f"(efficiency = {max_eff:.4f}), but endpoint advantage too small."
        )

    print(f"Verdict: {verdict}")
    print()

    # Efficiency variation analysis
    eff_range = max_eff - float(np.min(eff_arr))
    eff_mean = float(np.mean(eff_arr))
    eff_cv = float(np.std(eff_arr) / eff_mean) * 100  # coefficient of variation %

    print(f"efficiency range          : {eff_range:.6f} ({eff_range/eff_mean*100:.3f}% of mean)")
    print(f"efficiency mean           : {eff_mean:.6f}")
    print(f"efficiency std            : {float(np.std(eff_arr)):.6f}")
    print(f"coefficient of variation  : {eff_cv:.4f}%")
    print()

    # Key comparison
    print("KEY COMPARISON: Bloch-Redfield vs Phenomenological Lindblad")
    print("-" * 70)
    print(f"Phenomenological Phase 2 ENAQT peak: gamma/kappa ~ 41")
    print(f"Bloch-Redfield peak efficiency at:   lambda = {max_lam:.2f} cm^-1 "
          f"(gamma/kappa = {max_gk:.4f})")
    print(f"Physiological point:                 gamma/kappa = {phys_gk:.4f} "
          f"(lambda ~ 35 cm^-1)")
    print()

    # Physical interpretation
    is_flat = eff_range < 0.02  # less than 2% variation
    if is_flat:
        print("PHYSICAL INTERPRETATION:")
        print("-" * 70)
        print(f"  The Bloch-Redfield model shows transport efficiency is nearly FLAT")
        print(f"  across the entire bath strength range ({args.lambda_min_cm}-{args.lambda_max_cm} cm^-1),")
        print(f"  varying by only {eff_range:.4f} ({eff_range/eff_mean*100:.2f}%).")
        print()
        print(f"  This contrasts sharply with Phase 2's phenomenological Lindblad model,")
        print(f"  which showed a pronounced ENAQT peak at gamma/kappa ~ 41.")
        print()
        print(f"  The physical reason: when dissipation rates are derived from the")
        print(f"  ACTUAL spectral density at ACTUAL eigenstate gaps (as in Bloch-Redfield),")
        print(f"  the system maintains near-optimal transport efficiency across a wide")
        print(f"  range of bath coupling strengths. The Drude-Lorentz spectral density")
        print(f"  at physiological temperature (310K, kT={kT_rad_ps:.1f} rad/ps) gives")
        print(f"  rates that naturally satisfy detailed balance and thermalize")
        print(f"  eigenstate populations efficiently.")
        print()
        print(f"  At physiological parameters (lambda ~ 35 cm^-1), the efficiency")
        print(f"  is {phys_eff:.4f}, which is {phys_eff/max_eff*100:.1f}% of the maximum.")
        print(f"  This means the microtubule chromophore network operates near its")
        print(f"  optimal transport capacity regardless of exact bath parameters.")
    else:
        if abs(max_gk - phys_gk) / max(phys_gk, 1e-10) < 0.5:
            print(">>> The Bloch-Redfield peak is CLOSE to the physiological regime!")
        elif max_gk < phys_gk * 0.5:
            print(">>> The Bloch-Redfield peak is at LOWER gamma/kappa (higher dephasing) than physiological.")
        else:
            print(">>> The Bloch-Redfield peak is at HIGHER gamma/kappa (lower dephasing) than physiological.")

    # 5. Write CSV if requested
    if args.csv_out is not None:
        import csv
        with args.csv_out.open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "lambda_cm",
                    "lambda_rad_ps",
                    "kappa_eff_ps_inv",
                    "gamma_over_kappa",
                    "efficiency",
                ],
            )
            writer.writeheader()
            for i in range(len(lambdas_cm)):
                gk = V / kappa_effectives[i] if kappa_effectives[i] > 1e-15 else float("inf")
                writer.writerow({
                    "lambda_cm": f"{lambdas_cm[i]:.12g}",
                    "lambda_rad_ps": f"{cm_to_rad_ps(lambdas_cm[i]):.12g}",
                    "kappa_eff_ps_inv": f"{kappa_effectives[i]:.12g}",
                    "gamma_over_kappa": f"{gk:.12g}",
                    "efficiency": f"{efficiencies[i]:.12g}",
                })
        print()
        print(f"wrote_csv                 : {args.csv_out}")


if __name__ == "__main__":
    main()
