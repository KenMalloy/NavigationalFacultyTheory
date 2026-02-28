"""
Reverse-engineer the ENVIRONMENT that makes the real microtubule geometry
quantum-optimal.

Previous work showed:
  - At default bath (lambda=35, gamma_c=53, T=310K), the real MT geometry
    gives only ~0.17% quantum advantage.
  - A GA found that with the right GEOMETRY, 10.9% advantage is achievable
    at those bath parameters.

Now we flip it: fix the geometry at real MT values and search for the
bath/environment parameters where this geometry produces MAXIMUM quantum
advantage.

Part 1: Evolve Drude-Lorentz bath parameters (lambda, gamma_c)
Part 2: Evolve structured spectral density (Drude-Lorentz + Brownian oscillator)
"""

from __future__ import annotations

import time

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import differential_evolution

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    rad_ps_to_cm,
    KB_OVER_HBAR_PS_K,
)


# -----------------------------------------------------------------------
# Fixed geometry: real microtubule parameters
# -----------------------------------------------------------------------

SITES = 8
COUPLING_CM = 60.0
DISORDER_CM = 25.0
SEED = 7
HELIX_RADIUS_NM = 2.0
HELIX_RISE_NM = 0.8
HELIX_TWIST_DEG = 27.7
DIPOLE_TILT_DEG = 20.0

TEMPERATURE_K = 310.0

SINK_SITE = 7         # last site (0-indexed)
SINK_RATE_CM = 1.0
SOURCE_SITE = 0

T_MAX_PS = 50.0
N_TIME_POINTS = 200


# -----------------------------------------------------------------------
# Lindblad operator derivation (matching quantum_vs_classical.py exactly)
# -----------------------------------------------------------------------

def derive_lindblad_operators_drude(
    H_chromophore: np.ndarray,
    bath_strength_rad_ps: float,
    cutoff_rad_ps: float,
    kT_rad_ps: float,
    sink_site: int,
    sink_rate_ps_inv: float,
):
    """
    Derive secular Redfield Lindblad operators from H using a Drude-Lorentz
    spectral density.  Matches quantum_vs_classical.py exactly.
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
            delta_E = eigvals[b] - eigvals[a]
            if delta_E < 1e-12:
                continue

            gamma_factor = 0.0
            for j in range(N):
                gamma_factor += abs(eigvecs[j, a] * eigvecs[j, b]) ** 2

            if gamma_factor < 1e-15:
                continue

            j_val = J_drude(delta_E)
            n_th = n_bose(delta_E)

            # Downhill rate (b -> a)
            rate_down = gamma_factor * j_val * (n_th + 1.0)
            # Uphill rate (a -> b)
            rate_up = gamma_factor * j_val * n_th

            if rate_down > 1e-15:
                op_arr = np.zeros((N_total, N_total), dtype=complex)
                for site_i in range(N):
                    for site_j in range(N):
                        op_arr[site_i, site_j] += (
                            np.sqrt(rate_down) * eigvecs[site_i, a]
                            * np.conj(eigvecs[site_j, b])
                        )
                collapse_ops.append(qutip.Qobj(op_arr))

            if rate_up > 1e-15:
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


def derive_lindblad_operators_structured(
    H_chromophore: np.ndarray,
    bath_strength_rad_ps: float,
    cutoff_rad_ps: float,
    bo_strength_rad_ps: float,
    bo_frequency_rad_ps: float,
    bo_width_rad_ps: float,
    kT_rad_ps: float,
    sink_site: int,
    sink_rate_ps_inv: float,
):
    """
    Derive secular Redfield Lindblad operators using a structured spectral
    density: Drude-Lorentz + Brownian oscillator.

    J(omega) = J_DL(omega) + J_BO(omega)

    where J_BO(omega) = S * omega_0^2 * gamma_BO * omega
                        / ((omega^2 - omega_0^2)^2 + gamma_BO^2 * omega^2)
    """
    import qutip

    N = H_chromophore.shape[0]
    N_total = N + 1

    eigvals, eigvecs = eigh(H_chromophore)

    def J_total(omega):
        if omega <= 0:
            return 0.0
        # Drude-Lorentz
        j_dl = (2.0 * bath_strength_rad_ps * cutoff_rad_ps * omega
                / (omega ** 2 + cutoff_rad_ps ** 2))
        # Brownian oscillator
        j_bo = (bo_strength_rad_ps * bo_frequency_rad_ps ** 2
                * bo_width_rad_ps * omega
                / ((omega ** 2 - bo_frequency_rad_ps ** 2) ** 2
                   + bo_width_rad_ps ** 2 * omega ** 2))
        return j_dl + j_bo

    def n_bose(omega):
        if abs(omega) < 1e-12:
            return kT_rad_ps / (omega + 1e-30)
        x = omega / kT_rad_ps
        if x > 500:
            return 0.0
        return 1.0 / (np.exp(x) - 1.0)

    collapse_ops = []

    for a in range(N):
        for b in range(a + 1, N):
            delta_E = eigvals[b] - eigvals[a]
            if delta_E < 1e-12:
                continue

            gamma_factor = 0.0
            for j in range(N):
                gamma_factor += abs(eigvecs[j, a] * eigvecs[j, b]) ** 2

            if gamma_factor < 1e-15:
                continue

            j_val = J_total(delta_E)
            n_th = n_bose(delta_E)

            rate_down = gamma_factor * j_val * (n_th + 1.0)
            rate_up = gamma_factor * j_val * n_th

            if rate_down > 1e-15:
                op_arr = np.zeros((N_total, N_total), dtype=complex)
                for site_i in range(N):
                    for site_j in range(N):
                        op_arr[site_i, site_j] += (
                            np.sqrt(rate_down) * eigvecs[site_i, a]
                            * np.conj(eigvecs[site_j, b])
                        )
                collapse_ops.append(qutip.Qobj(op_arr))

            if rate_up > 1e-15:
                op_arr = np.zeros((N_total, N_total), dtype=complex)
                for site_i in range(N):
                    for site_j in range(N):
                        op_arr[site_i, site_j] += (
                            np.sqrt(rate_up) * eigvecs[site_i, b]
                            * np.conj(eigvecs[site_j, a])
                        )
                collapse_ops.append(qutip.Qobj(op_arr))

    # Pure dephasing: use the total J at omega->0+ limit
    # For Drude-Lorentz: J(0+)/omega -> 2*lambda/gamma_c, so S(0) = 4*lambda*kT/gamma_c
    # For Brownian oscillator: J_BO(0+)/omega -> S*gamma_BO/omega_0^2
    # So S_zero_total = S_zero_DL + S_zero_BO
    S_zero_dl = 4.0 * bath_strength_rad_ps * kT_rad_ps / cutoff_rad_ps
    if bo_frequency_rad_ps > 1e-12:
        S_zero_bo = 4.0 * bo_strength_rad_ps * bo_width_rad_ps * kT_rad_ps / (bo_frequency_rad_ps ** 2)
    else:
        S_zero_bo = 0.0
    S_zero = S_zero_dl + S_zero_bo

    for j in range(N):
        diag_elements = np.array([abs(eigvecs[j, a]) ** 2 for a in range(N)])
        if np.max(np.abs(diag_elements)) < 1e-15:
            continue

        op_eig = np.diag(diag_elements) * np.sqrt(S_zero)
        op_site = eigvecs @ op_eig @ eigvecs.conj().T

        op_ext = np.zeros((N_total, N_total), dtype=complex)
        op_ext[:N, :N] = op_site
        collapse_ops.append(qutip.Qobj(op_ext))

    # Sink
    c_arr = np.zeros((N_total, N_total), dtype=float)
    c_arr[N, sink_site] = np.sqrt(sink_rate_ps_inv)
    collapse_ops.append(qutip.Qobj(c_arr))

    return collapse_ops, eigvals, eigvecs


# -----------------------------------------------------------------------
# Transport efficiency computation
# -----------------------------------------------------------------------

def compute_efficiency(H_chromophore, alpha, collapse_ops, source_site,
                       t_max, n_time_points):
    """Run mesolve and return trap population at t_max."""
    import qutip

    N = H_chromophore.shape[0]
    N_total = N + 1

    H_ext = np.zeros((N_total, N_total), dtype=complex)
    H_ext[:N, :N] = alpha * H_chromophore
    H_qobj = qutip.Qobj(H_ext)

    psi0 = qutip.basis(N_total, source_site)
    tlist = np.linspace(0, t_max, n_time_points)

    result = qutip.mesolve(H_qobj, psi0, tlist, c_ops=collapse_ops)

    rho_final = result.states[-1]
    efficiency = float(np.real(rho_final[N, N]))
    return efficiency


def quantum_advantage_drude(params, H, kT_rad_ps, sink_rate, model_cache):
    """
    Compute quantum advantage for given Drude-Lorentz bath parameters.
    Returns NEGATIVE advantage (for minimization).
    """
    bath_strength_cm, cutoff_cm = params

    bath_strength_rad_ps = cm_to_rad_ps(bath_strength_cm)
    cutoff_rad_ps = cm_to_rad_ps(cutoff_cm)

    try:
        collapse_ops, _, _ = derive_lindblad_operators_drude(
            H_chromophore=H,
            bath_strength_rad_ps=bath_strength_rad_ps,
            cutoff_rad_ps=cutoff_rad_ps,
            kT_rad_ps=kT_rad_ps,
            sink_site=SINK_SITE,
            sink_rate_ps_inv=sink_rate,
        )

        eff_quantum = compute_efficiency(
            H, 1.0, collapse_ops, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
        eff_classical = compute_efficiency(
            H, 0.0, collapse_ops, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)

        advantage = eff_quantum - eff_classical

        # Track the best so far
        if advantage > model_cache.get("best_advantage", -np.inf):
            model_cache["best_advantage"] = advantage
            model_cache["best_params"] = params.copy()
            model_cache["best_eff_q"] = eff_quantum
            model_cache["best_eff_c"] = eff_classical
            print(f"  [DL] New best: lambda={bath_strength_cm:.1f}, "
                  f"gamma_c={cutoff_cm:.1f} -> "
                  f"advantage={advantage*100:.3f}% "
                  f"(Q={eff_quantum:.4f}, C={eff_classical:.4f})")

        return -advantage  # minimize negative = maximize advantage

    except Exception as e:
        print(f"  [DL] Error at lambda={bath_strength_cm:.1f}, "
              f"gamma_c={cutoff_cm:.1f}: {e}")
        return 0.0  # no advantage


def quantum_advantage_structured(params, H, kT_rad_ps, sink_rate, model_cache):
    """
    Compute quantum advantage for structured bath (DL + BO).
    Returns NEGATIVE advantage (for minimization).
    """
    bath_strength_cm, cutoff_cm, bo_strength_cm, bo_frequency_cm, bo_width_cm = params

    bath_strength_rad_ps = cm_to_rad_ps(bath_strength_cm)
    cutoff_rad_ps = cm_to_rad_ps(cutoff_cm)
    bo_strength_rad_ps = cm_to_rad_ps(bo_strength_cm)
    bo_frequency_rad_ps = cm_to_rad_ps(bo_frequency_cm)
    bo_width_rad_ps = cm_to_rad_ps(bo_width_cm)

    try:
        collapse_ops, _, _ = derive_lindblad_operators_structured(
            H_chromophore=H,
            bath_strength_rad_ps=bath_strength_rad_ps,
            cutoff_rad_ps=cutoff_rad_ps,
            bo_strength_rad_ps=bo_strength_rad_ps,
            bo_frequency_rad_ps=bo_frequency_rad_ps,
            bo_width_rad_ps=bo_width_rad_ps,
            kT_rad_ps=kT_rad_ps,
            sink_site=SINK_SITE,
            sink_rate_ps_inv=sink_rate,
        )

        eff_quantum = compute_efficiency(
            H, 1.0, collapse_ops, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
        eff_classical = compute_efficiency(
            H, 0.0, collapse_ops, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)

        advantage = eff_quantum - eff_classical

        if advantage > model_cache.get("best_advantage", -np.inf):
            model_cache["best_advantage"] = advantage
            model_cache["best_params"] = params.copy()
            model_cache["best_eff_q"] = eff_quantum
            model_cache["best_eff_c"] = eff_classical
            print(f"  [BO] New best: lambda={bath_strength_cm:.1f}, "
                  f"gamma_c={cutoff_cm:.1f}, "
                  f"S={bo_strength_cm:.1f}, "
                  f"w0={bo_frequency_cm:.1f}, "
                  f"gBO={bo_width_cm:.1f} -> "
                  f"advantage={advantage*100:.3f}% "
                  f"(Q={eff_quantum:.4f}, C={eff_classical:.4f})")

        return -advantage

    except Exception as e:
        print(f"  [BO] Error: {e}")
        return 0.0


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("REVERSE ENGINEERING: What ENVIRONMENT makes the real")
    print("microtubule geometry quantum-optimal?")
    print("=" * 72)
    print()

    # ---------------------------------------------------------------
    # Setup: build model with fixed real MT geometry
    # ---------------------------------------------------------------

    sink_rate = cm_to_rad_ps(SINK_RATE_CM)
    kT_rad_ps = KB_OVER_HBAR_PS_K * TEMPERATURE_K

    model = build_helix_model(
        sites=SITES,
        coupling_cm=COUPLING_CM,
        disorder_cm=DISORDER_CM,
        seed=SEED,
        helix_radius_nm=HELIX_RADIUS_NM,
        helix_rise_nm=HELIX_RISE_NM,
        helix_twist_deg=HELIX_TWIST_DEG,
        dipole_tilt_deg=DIPOLE_TILT_DEG,
    )

    H = model.hamiltonian

    print("Fixed geometry (real microtubule):")
    print(f"  sites={SITES}, coupling={COUPLING_CM} cm-1, "
          f"disorder={DISORDER_CM} cm-1, seed={SEED}")
    print(f"  helix: radius={HELIX_RADIUS_NM} nm, rise={HELIX_RISE_NM} nm, "
          f"twist={HELIX_TWIST_DEG} deg, tilt={DIPOLE_TILT_DEG} deg")
    print(f"  temperature={TEMPERATURE_K} K (fixed)")
    print(f"  model: {model.label}")
    print()

    # Eigenstate analysis
    eigvals, eigvecs = eigh(H)
    eigvals_cm = rad_ps_to_cm(eigvals)
    gaps = np.diff(eigvals)
    gaps_cm = rad_ps_to_cm(gaps)

    print("Eigenstates of H:")
    for i, e_cm in enumerate(eigvals_cm):
        print(f"  |{i}> : {e_cm:10.4f} cm^-1")
    print()
    print("Eigenstate gaps:")
    for i, g_cm in enumerate(gaps_cm):
        print(f"  |{i}> -> |{i+1}> : {g_cm:10.4f} cm^-1")
    print()

    gap_min_cm = float(np.min(gaps_cm))
    gap_max_cm = float(np.max(gaps_cm))
    gap_median_cm = float(np.median(gaps_cm))
    print(f"  Gap range: {gap_min_cm:.2f} - {gap_max_cm:.2f} cm^-1")
    print(f"  Median gap: {gap_median_cm:.2f} cm^-1")
    print()

    # ---------------------------------------------------------------
    # Baseline: default bath parameters
    # ---------------------------------------------------------------

    print("=" * 72)
    print("BASELINE: Default bath (lambda=35, gamma_c=53, T=310K)")
    print("=" * 72)
    print()

    bath_strength_default = cm_to_rad_ps(35.0)
    cutoff_default = cm_to_rad_ps(53.0)

    collapse_ops_default, _, _ = derive_lindblad_operators_drude(
        H_chromophore=H,
        bath_strength_rad_ps=bath_strength_default,
        cutoff_rad_ps=cutoff_default,
        kT_rad_ps=kT_rad_ps,
        sink_site=SINK_SITE,
        sink_rate_ps_inv=sink_rate,
    )

    eff_q_default = compute_efficiency(
        H, 1.0, collapse_ops_default, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
    eff_c_default = compute_efficiency(
        H, 0.0, collapse_ops_default, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
    adv_default = eff_q_default - eff_c_default

    print(f"  Quantum efficiency  (alpha=1): {eff_q_default:.6f}")
    print(f"  Classical efficiency (alpha=0): {eff_c_default:.6f}")
    print(f"  Quantum advantage: {adv_default:+.6f} ({adv_default/eff_c_default*100:+.2f}%)")
    print()

    # ===============================================================
    # PART 1: Evolve Drude-Lorentz bath parameters
    # ===============================================================

    print("=" * 72)
    print("PART 1: Evolve Drude-Lorentz bath parameters")
    print("  Searching for (lambda, gamma_c) that maximizes quantum advantage")
    print("  Temperature fixed at 310 K")
    print("  GA: maxiter=30, popsize=12, seed=42")
    print("=" * 72)
    print()

    bounds_dl = [
        (1.0, 200.0),    # bath_strength_cm (lambda)
        (5.0, 500.0),    # cutoff_cm (gamma_c)
    ]

    cache_dl = {}

    t0 = time.time()
    result_dl = differential_evolution(
        func=quantum_advantage_drude,
        bounds=bounds_dl,
        args=(H, kT_rad_ps, sink_rate, cache_dl),
        maxiter=30,
        popsize=12,
        seed=42,
        tol=1e-8,
        disp=False,
    )
    dt_dl = time.time() - t0

    opt_lambda_cm = result_dl.x[0]
    opt_gamma_c_cm = result_dl.x[1]
    opt_advantage_dl = -result_dl.fun

    # Recompute efficiencies at optimal
    bath_str_opt = cm_to_rad_ps(opt_lambda_cm)
    cutoff_opt = cm_to_rad_ps(opt_gamma_c_cm)

    collapse_ops_opt, _, _ = derive_lindblad_operators_drude(
        H_chromophore=H,
        bath_strength_rad_ps=bath_str_opt,
        cutoff_rad_ps=cutoff_opt,
        kT_rad_ps=kT_rad_ps,
        sink_site=SINK_SITE,
        sink_rate_ps_inv=sink_rate,
    )
    eff_q_opt = compute_efficiency(
        H, 1.0, collapse_ops_opt, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
    eff_c_opt = compute_efficiency(
        H, 0.0, collapse_ops_opt, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)

    print()
    print(f"  Optimization completed in {dt_dl:.1f} s")
    print(f"  Optimal Drude-Lorentz parameters:")
    print(f"    lambda (reorganization energy) = {opt_lambda_cm:.2f} cm^-1")
    print(f"    gamma_c (bath cutoff freq)     = {opt_gamma_c_cm:.2f} cm^-1")
    print(f"    temperature                    = {TEMPERATURE_K:.0f} K (fixed)")
    print(f"  Quantum efficiency  (alpha=1):   {eff_q_opt:.6f}")
    print(f"  Classical efficiency (alpha=0):   {eff_c_opt:.6f}")
    print(f"  QUANTUM ADVANTAGE:               {opt_advantage_dl:+.6f} ({opt_advantage_dl/max(eff_c_opt,1e-10)*100:+.2f}%)")
    print(f"  Improvement over default:        {opt_advantage_dl/max(adv_default,1e-10):.1f}x")
    print()

    # ===============================================================
    # PART 2: Structured spectral density (DL + Brownian oscillator)
    # ===============================================================

    print("=" * 72)
    print("PART 2: Evolve structured bath (Drude-Lorentz + Brownian oscillator)")
    print("  J(w) = J_DL(w) + J_BO(w)")
    print("  J_BO(w) = S*w0^2*gBO*w / ((w^2-w0^2)^2 + gBO^2*w^2)")
    print("  GA: maxiter=30, popsize=12, seed=42")
    print("=" * 72)
    print()

    bounds_bo = [
        (1.0, 200.0),    # bath_strength_cm (lambda)
        (5.0, 500.0),    # cutoff_cm (gamma_c)
        (0.0, 200.0),    # bo_strength_cm (S)
        (10.0, 300.0),   # bo_frequency_cm (omega_0)
        (5.0, 100.0),    # bo_width_cm (gamma_BO)
    ]

    cache_bo = {}

    t0 = time.time()
    result_bo = differential_evolution(
        func=quantum_advantage_structured,
        bounds=bounds_bo,
        args=(H, kT_rad_ps, sink_rate, cache_bo),
        maxiter=30,
        popsize=12,
        seed=42,
        tol=1e-8,
        disp=False,
    )
    dt_bo = time.time() - t0

    opt_lambda_bo = result_bo.x[0]
    opt_gamma_c_bo = result_bo.x[1]
    opt_S_bo = result_bo.x[2]
    opt_w0_bo = result_bo.x[3]
    opt_gBO_bo = result_bo.x[4]
    opt_advantage_bo = -result_bo.fun

    # Recompute efficiencies at optimal
    bath_str_bo = cm_to_rad_ps(opt_lambda_bo)
    cutoff_bo = cm_to_rad_ps(opt_gamma_c_bo)
    bo_str = cm_to_rad_ps(opt_S_bo)
    bo_freq = cm_to_rad_ps(opt_w0_bo)
    bo_wid = cm_to_rad_ps(opt_gBO_bo)

    collapse_ops_bo, _, _ = derive_lindblad_operators_structured(
        H_chromophore=H,
        bath_strength_rad_ps=bath_str_bo,
        cutoff_rad_ps=cutoff_bo,
        bo_strength_rad_ps=bo_str,
        bo_frequency_rad_ps=bo_freq,
        bo_width_rad_ps=bo_wid,
        kT_rad_ps=kT_rad_ps,
        sink_site=SINK_SITE,
        sink_rate_ps_inv=sink_rate,
    )
    eff_q_bo = compute_efficiency(
        H, 1.0, collapse_ops_bo, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)
    eff_c_bo = compute_efficiency(
        H, 0.0, collapse_ops_bo, SOURCE_SITE, T_MAX_PS, N_TIME_POINTS)

    print()
    print(f"  Optimization completed in {dt_bo:.1f} s")
    print(f"  Optimal structured bath parameters:")
    print(f"    lambda (reorganization energy) = {opt_lambda_bo:.2f} cm^-1")
    print(f"    gamma_c (bath cutoff freq)     = {opt_gamma_c_bo:.2f} cm^-1")
    print(f"    S (BO peak strength)           = {opt_S_bo:.2f} cm^-1")
    print(f"    omega_0 (BO peak frequency)    = {opt_w0_bo:.2f} cm^-1")
    print(f"    gamma_BO (BO peak width)       = {opt_gBO_bo:.2f} cm^-1")
    print(f"    temperature                    = {TEMPERATURE_K:.0f} K (fixed)")
    print(f"  Quantum efficiency  (alpha=1):   {eff_q_bo:.6f}")
    print(f"  Classical efficiency (alpha=0):   {eff_c_bo:.6f}")
    print(f"  QUANTUM ADVANTAGE:               {opt_advantage_bo:+.6f} ({opt_advantage_bo/max(eff_c_bo,1e-10)*100:+.2f}%)")
    print(f"  Improvement over default:        {opt_advantage_bo/max(adv_default,1e-10):.1f}x")
    print(f"  Improvement over DL-only:        {opt_advantage_bo/max(opt_advantage_dl,1e-10):.1f}x")
    print()

    # ===============================================================
    # Spectral density profile at optimal structured bath
    # ===============================================================

    print("=" * 72)
    print("SPECTRAL DENSITY at optimal structured bath parameters")
    print("=" * 72)
    print()

    # Show J(omega) at 10 frequencies spanning eigenstate gap range
    gap_freqs_cm = np.linspace(
        max(gap_min_cm * 0.5, 1.0),
        gap_max_cm * 1.5,
        10
    )

    print(f"  {'omega (cm^-1)':>14}  {'J_DL':>12}  {'J_BO':>12}  {'J_total':>12}")
    print(f"  {'-'*14}  {'-'*12}  {'-'*12}  {'-'*12}")

    for w_cm in gap_freqs_cm:
        w = cm_to_rad_ps(w_cm)
        j_dl = (2.0 * bath_str_bo * cutoff_bo * w
                / (w ** 2 + cutoff_bo ** 2))
        j_bo_val = (bo_str * bo_freq ** 2 * bo_wid * w
                    / ((w ** 2 - bo_freq ** 2) ** 2
                       + bo_wid ** 2 * w ** 2))
        j_total = j_dl + j_bo_val
        # Convert back to cm^-1 units for display
        j_dl_cm = rad_ps_to_cm(j_dl)
        j_bo_cm = rad_ps_to_cm(j_bo_val)
        j_total_cm = rad_ps_to_cm(j_total)
        print(f"  {w_cm:14.2f}  {j_dl_cm:12.4f}  {j_bo_cm:12.4f}  {j_total_cm:12.4f}")

    print()
    print(f"  Eigenstate gap range: {gap_min_cm:.2f} - {gap_max_cm:.2f} cm^-1")
    print(f"  BO peak center: {opt_w0_bo:.2f} cm^-1")
    if gap_min_cm <= opt_w0_bo <= gap_max_cm:
        print(f"  -> BO peak falls WITHIN the eigenstate gap range!")
    elif opt_w0_bo < gap_min_cm:
        print(f"  -> BO peak is BELOW the eigenstate gap range")
    else:
        print(f"  -> BO peak is ABOVE the eigenstate gap range")
    print()

    # ===============================================================
    # Physical reasonableness assessment
    # ===============================================================

    print("=" * 72)
    print("PHYSICAL REASONABLENESS ASSESSMENT")
    print("=" * 72)
    print()

    # Drude-Lorentz optimal
    print("Optimal Drude-Lorentz bath:")
    print(f"  lambda = {opt_lambda_cm:.2f} cm^-1", end="")
    if 10 <= opt_lambda_cm <= 100:
        print("  [REASONABLE: 10-100 cm^-1 typical for proteins]")
    elif opt_lambda_cm < 10:
        print("  [LOW: below typical protein range]")
    else:
        print("  [HIGH: above typical protein range]")

    print(f"  gamma_c = {opt_gamma_c_cm:.2f} cm^-1", end="")
    if 50 <= opt_gamma_c_cm <= 200:
        print("  [REASONABLE: 50-200 cm^-1 typical]")
    elif opt_gamma_c_cm < 50:
        print("  [SLOW BATH: unusually long correlation time]")
    else:
        print("  [FAST BATH: unusually short correlation time]")

    bath_corr_time_ps = 1.0 / cm_to_rad_ps(opt_gamma_c_cm)
    print(f"  Bath correlation time = {bath_corr_time_ps:.3f} ps "
          f"(= 1/gamma_c)")
    print()

    # Structured bath optimal
    print("Optimal structured bath:")
    print(f"  lambda = {opt_lambda_bo:.2f} cm^-1", end="")
    if 10 <= opt_lambda_bo <= 100:
        print("  [REASONABLE]")
    elif opt_lambda_bo < 10:
        print("  [LOW]")
    else:
        print("  [HIGH]")

    print(f"  gamma_c = {opt_gamma_c_bo:.2f} cm^-1", end="")
    if 50 <= opt_gamma_c_bo <= 200:
        print("  [REASONABLE]")
    elif opt_gamma_c_bo < 50:
        print("  [SLOW BATH]")
    else:
        print("  [FAST BATH]")

    print(f"  S (BO strength) = {opt_S_bo:.2f} cm^-1", end="")
    if opt_S_bo <= 5 * opt_lambda_bo:
        print(f"  [REASONABLE: S/lambda = {opt_S_bo/max(opt_lambda_bo,1e-10):.1f} <= 5]")
    else:
        print(f"  [HIGH: S/lambda = {opt_S_bo/max(opt_lambda_bo,1e-10):.1f} > 5]")

    print(f"  omega_0 (BO peak) = {opt_w0_bo:.2f} cm^-1", end="")
    if 50 <= opt_w0_bo <= 250:
        print("  [REASONABLE: corresponds to protein vibrational modes]")
        # Identify likely mode
        if opt_w0_bo < 100:
            print("    (possible: hydrogen bond bending, backbone torsions)")
        elif opt_w0_bo < 180:
            print("    (possible: hydrogen bond stretches, amide VI)")
        else:
            print("    (possible: amide bands, C-C stretches)")
    elif opt_w0_bo < 50:
        print("  [LOW: below typical protein modes]")
    else:
        print("  [HIGH: above typical low-frequency protein modes]")

    print(f"  gamma_BO (BO width) = {opt_gBO_bo:.2f} cm^-1", end="")
    quality_factor = opt_w0_bo / max(opt_gBO_bo, 1e-10)
    print(f"  [Q-factor = {quality_factor:.1f}]")
    if quality_factor > 5:
        print("    (sharp, well-defined vibrational mode)")
    elif quality_factor > 1:
        print("    (moderately damped vibrational mode)")
    else:
        print("    (overdamped, broad feature)")
    print()

    # ===============================================================
    # SUMMARY
    # ===============================================================

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print()
    print(f"  Default bath (lambda=35, gamma_c=53):")
    print(f"    Quantum advantage = {adv_default*100:+.3f}%")
    print()
    print(f"  Optimal Drude-Lorentz bath:")
    print(f"    lambda={opt_lambda_cm:.1f}, gamma_c={opt_gamma_c_cm:.1f}")
    print(f"    Quantum advantage = {opt_advantage_dl*100:+.3f}%")
    print(f"    ({opt_advantage_dl/max(adv_default,1e-10):.1f}x improvement)")
    print()
    print(f"  Optimal structured bath (DL + Brownian oscillator):")
    print(f"    lambda={opt_lambda_bo:.1f}, gamma_c={opt_gamma_c_bo:.1f}, "
          f"S={opt_S_bo:.1f}, w0={opt_w0_bo:.1f}, gBO={opt_gBO_bo:.1f}")
    print(f"    Quantum advantage = {opt_advantage_bo*100:+.3f}%")
    print(f"    ({opt_advantage_bo/max(adv_default,1e-10):.1f}x improvement)")
    print()

    # Interpretation
    print("=" * 72)
    print("PHYSICAL INTERPRETATION")
    print("=" * 72)
    print()

    if opt_advantage_dl > 3 * adv_default:
        print("  The real MT geometry CAN produce significant quantum advantage")
        print("  if the environment is tuned appropriately.")
        print()
        if opt_lambda_cm < 30:
            print("  The optimal environment has WEAKER system-bath coupling than")
            print("  the default. This suggests the default bath overwhelms")
            print("  quantum coherence — a slightly quieter environment would")
            print("  allow the MT geometry to exploit coherent transport.")
        elif opt_lambda_cm > 40:
            print("  The optimal environment has STRONGER system-bath coupling.")
            print("  This suggests ENAQT: the bath needs to be stronger to")
            print("  enable noise-assisted transport through the MT geometry.")
        else:
            print("  The optimal lambda is similar to the default, suggesting")
            print("  the key parameter is the bath timescale (gamma_c).")

        if opt_gamma_c_cm < 40:
            print("  The optimal bath has a LONGER correlation time (slower bath).")
            print("  A more structured, slower environment preserves coherence")
            print("  long enough for quantum transport to help.")
        elif opt_gamma_c_cm > 70:
            print("  The optimal bath has a SHORTER correlation time (faster bath).")
            print("  A more Markovian environment is better for quantum transport")
            print("  through the MT geometry.")
    else:
        print("  Even with optimal DL bath parameters, the quantum advantage")
        print("  remains small. The real MT geometry may not be optimized")
        print("  for quantum transport under any simple bath model.")

    print()

    if opt_advantage_bo > opt_advantage_dl * 1.5:
        print("  The Brownian oscillator SIGNIFICANTLY boosts quantum advantage!")
        print(f"  Adding a peaked spectral density at {opt_w0_bo:.1f} cm^-1")
        print(f"  increases the advantage from {opt_advantage_dl*100:.3f}% to "
              f"{opt_advantage_bo*100:.3f}%.")
        print()
        print("  This suggests that a specific protein vibrational mode")
        print("  could be tuned to enhance quantum transport in microtubules.")
        print("  The key frequency is {:.1f} cm^-1, which would correspond to:".format(opt_w0_bo))
        if 50 <= opt_w0_bo <= 100:
            print("    - Hydrogen bond bending modes")
            print("    - Low-frequency backbone torsions")
        elif 100 < opt_w0_bo <= 200:
            print("    - Hydrogen bond stretching modes")
            print("    - Amide VI modes")
        elif 200 < opt_w0_bo <= 300:
            print("    - C-C stretching modes")
            print("    - Amide V modes")
        else:
            print("    - (outside typical protein vibrational range)")
    elif opt_advantage_bo > opt_advantage_dl * 1.1:
        print("  The Brownian oscillator provides a modest additional boost.")
        print("  Structured noise helps somewhat but is not transformative.")
    else:
        print("  The Brownian oscillator does NOT significantly improve")
        print("  quantum advantage beyond what the DL bath achieves.")
        print("  The environment's broad spectral properties matter more")
        print("  than any specific vibrational mode.")

    print()
    print("=" * 72)
    print("END OF REVERSE ENGINEERING ANALYSIS")
    print("=" * 72)


if __name__ == "__main__":
    main()
