"""
Phase 3: Evolutionary search for microtubule geometries that MAXIMIZE
quantum advantage in transport.

Uses scipy.optimize.differential_evolution to search over helix geometry
parameters. The fitness function is:

    fitness = efficiency(alpha=1) - efficiency(alpha=0)

i.e., quantum advantage = transport with full Hamiltonian minus transport
with H=0 (same bath-derived Lindblad operators, no coherent dynamics).

For each candidate geometry:
1. Build helix model with candidate geometry params
2. Diagonalize H to get eigenstates and eigenvalues
3. Derive Bloch-Redfield rates from Drude-Lorentz spectral density J(w)
4. Build Lindblad operators for population transfer (secular Redfield)
5. Add pure dephasing from J(0+) limit
6. Add sink operator on last site: L_sink = sqrt(Gamma) |trap><last_site|
   The L rho L^dag term deposits population into the trap; the anti-commutator
   term -{Gamma/2}{|s><s|, rho} drains it from the sink site.
   This is non-trace-preserving in the chromophore subspace.
7. Run mesolve with full H + all collapse ops -> efficiency_quantum
8. Run mesolve with H=0 + same collapse ops -> efficiency_classical
9. Return efficiency_quantum - efficiency_classical
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
# Fixed parameters
# -----------------------------------------------------------------------

SITES = 8
SEED = 7
BATH_STRENGTH_CM = 35.0
CUTOFF_CM = 53.0
TEMPERATURE_K = 310.0
SINK_RATE_CM = 1.0
SOURCE_SITE = 0
T_MAX_PS = 50.0
N_TIME_POINTS = 200

# GA parameters
GA_MAXITER = 30
GA_POPSIZE = 10
GA_SEED = 42

# Default geometry for comparison
DEFAULT_GEOMETRY = {
    "helix_radius_nm": 2.0,
    "helix_rise_nm": 0.8,
    "helix_twist_deg": 27.7,
    "dipole_tilt_deg": 20.0,
    "disorder_cm": 25.0,
    "coupling_cm": 60.0,
}

# Bounds for GA search
BOUNDS = [
    (1.0, 5.0),    # helix_radius_nm
    (0.3, 2.0),    # helix_rise_nm
    (15.0, 50.0),  # helix_twist_deg
    (0.0, 60.0),   # dipole_tilt_deg
    (0.0, 150.0),  # disorder_cm
    (20.0, 200.0), # coupling_cm
]

PARAM_NAMES = [
    "helix_radius_nm",
    "helix_rise_nm",
    "helix_twist_deg",
    "dipole_tilt_deg",
    "disorder_cm",
    "coupling_cm",
]


# -----------------------------------------------------------------------
# Derive Lindblad operators (reuses quantum_vs_classical.py approach)
# -----------------------------------------------------------------------

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

    The sink is implemented as L_sink = sqrt(Gamma) |trap><sink_site|.
    This removes population from the sink site (anti-commutator decay)
    and deposits it in the trap (L rho L^dag recycling into trap).
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
    # This implements the sink with anti-commutator decay on the sink site
    # and population recycling into the trap site.
    c_arr = np.zeros((N_total, N_total), dtype=float)
    c_arr[N, sink_site] = np.sqrt(sink_rate_ps_inv)
    collapse_ops.append(qutip.Qobj(c_arr))

    return collapse_ops, eigvals, eigvecs


# -----------------------------------------------------------------------
# Run mesolve with Hamiltonian scaling
# -----------------------------------------------------------------------

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


# -----------------------------------------------------------------------
# Compute quantum advantage for a given geometry
# -----------------------------------------------------------------------

def compute_quantum_advantage(
    sites: int,
    helix_radius_nm: float,
    helix_rise_nm: float,
    helix_twist_deg: float,
    dipole_tilt_deg: float,
    disorder_cm: float,
    coupling_cm: float,
    seed: int = SEED,
    bath_strength_cm: float = BATH_STRENGTH_CM,
    cutoff_cm: float = CUTOFF_CM,
    temperature_k: float = TEMPERATURE_K,
    sink_rate_cm: float = SINK_RATE_CM,
    t_max_ps: float = T_MAX_PS,
    n_time_points: int = N_TIME_POINTS,
) -> tuple[float, float, float]:
    """
    Compute quantum advantage for a given geometry.

    Returns (quantum_advantage, eff_quantum, eff_classical).
    """
    # Convert units
    sink_rate = cm_to_rad_ps(sink_rate_cm)
    cutoff_rad_ps = cm_to_rad_ps(cutoff_cm)
    kT_rad_ps = KB_OVER_HBAR_PS_K * temperature_k
    bath_strength_rad_ps = cm_to_rad_ps(bath_strength_cm)

    # Build helix model
    model = build_helix_model(
        sites=sites,
        coupling_cm=coupling_cm,
        disorder_cm=disorder_cm,
        seed=seed,
        helix_radius_nm=helix_radius_nm,
        helix_rise_nm=helix_rise_nm,
        helix_twist_deg=helix_twist_deg,
        dipole_tilt_deg=dipole_tilt_deg,
    )

    H = model.hamiltonian  # in rad/ps
    N = H.shape[0]
    sink_site = N - 1  # last site

    # Derive Lindblad operators from full Hamiltonian (alpha=1)
    # These are FIXED for both quantum and classical runs
    collapse_ops, eigvals, eigvecs = derive_lindblad_operators(
        H_chromophore=H,
        bath_strength_rad_ps=bath_strength_rad_ps,
        cutoff_rad_ps=cutoff_rad_ps,
        kT_rad_ps=kT_rad_ps,
        sink_site=sink_site,
        sink_rate_ps_inv=sink_rate,
    )

    # Quantum (alpha=1): full H + bath Lindblad + sink
    eff_quantum = run_with_hamiltonian_scaling(
        H_chromophore=H,
        alpha=1.0,
        collapse_ops=collapse_ops,
        source_site=SOURCE_SITE,
        t_max=t_max_ps,
        n_time_points=n_time_points,
    )

    # Classical (alpha=0): H=0 + same bath Lindblad + sink
    eff_classical = run_with_hamiltonian_scaling(
        H_chromophore=H,
        alpha=0.0,
        collapse_ops=collapse_ops,
        source_site=SOURCE_SITE,
        t_max=t_max_ps,
        n_time_points=n_time_points,
    )

    quantum_advantage = eff_quantum - eff_classical
    return quantum_advantage, eff_quantum, eff_classical


# -----------------------------------------------------------------------
# GA fitness function
# -----------------------------------------------------------------------

# Global counter for tracking evaluations
_eval_count = 0
_gen_best = -999.0
_gen_best_params = None
_gen_count = 0
_gen_start_eval = 0


def fitness_function(x):
    """
    Fitness function for differential_evolution.
    DE minimizes, so we return -quantum_advantage.
    """
    global _eval_count, _gen_best, _gen_best_params

    helix_radius_nm = x[0]
    helix_rise_nm = x[1]
    helix_twist_deg = x[2]
    dipole_tilt_deg = x[3]
    disorder_cm = x[4]
    coupling_cm = x[5]

    try:
        qa, eff_q, eff_c = compute_quantum_advantage(
            sites=SITES,
            helix_radius_nm=helix_radius_nm,
            helix_rise_nm=helix_rise_nm,
            helix_twist_deg=helix_twist_deg,
            dipole_tilt_deg=dipole_tilt_deg,
            disorder_cm=disorder_cm,
            coupling_cm=coupling_cm,
        )
    except Exception:
        # If simulation fails, return poor fitness
        qa = -1.0

    _eval_count += 1

    if qa > _gen_best:
        _gen_best = qa
        _gen_best_params = x.copy()

    return -qa  # DE minimizes, so negate


def ga_callback(xk, convergence):
    """Callback called after each generation of differential_evolution."""
    global _gen_count, _gen_best, _gen_best_params, _gen_start_eval, _eval_count

    _gen_count += 1

    if _gen_best_params is not None:
        params_str = (
            f"r={_gen_best_params[0]:.2f} rise={_gen_best_params[1]:.2f} "
            f"tw={_gen_best_params[2]:.1f} tilt={_gen_best_params[3]:.1f} "
            f"dis={_gen_best_params[4]:.1f} coup={_gen_best_params[5]:.1f}"
        )
    else:
        params_str = "N/A"

    print(
        f"  Gen {_gen_count:3d} | best QA = {_gen_best:+.6f} | "
        f"conv = {convergence:.4f} | evals = {_eval_count} | "
        f"{params_str}",
        flush=True,
    )

    _gen_start_eval = _eval_count


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    print("=" * 76)
    print("PHASE 3: EVOLUTIONARY SEARCH FOR MAXIMUM QUANTUM ADVANTAGE")
    print("=" * 76)
    print()
    print("Fitness = efficiency(alpha=1) - efficiency(alpha=0)")
    print("  alpha=1: full Hamiltonian + bath Lindblad + sink")
    print("  alpha=0: H=0 + same bath Lindblad + sink")
    print("  Sink: L_sink = sqrt(Gamma) |trap><last_site| (irreversible trapping)")
    print()
    print("Fixed parameters:")
    print(f"  sites          = {SITES}")
    print(f"  seed           = {SEED}")
    print(f"  bath_strength  = {BATH_STRENGTH_CM} cm^-1")
    print(f"  cutoff         = {CUTOFF_CM} cm^-1")
    print(f"  temperature    = {TEMPERATURE_K} K")
    print(f"  sink_rate      = {SINK_RATE_CM} cm^-1 ({cm_to_rad_ps(SINK_RATE_CM):.6f} rad/ps)")
    print(f"  T_max          = {T_MAX_PS} ps")
    print(f"  N_time_points  = {N_TIME_POINTS}")
    print()
    print("GA parameters:")
    print(f"  maxiter  = {GA_MAXITER}")
    print(f"  popsize  = {GA_POPSIZE}")
    print(f"  seed     = {GA_SEED}")
    print()
    print("Search bounds:")
    for name, (lo, hi) in zip(PARAM_NAMES, BOUNDS):
        print(f"  {name:20s}: [{lo:.1f}, {hi:.1f}]")
    print()

    # ---------------------------------------------------------------
    # Step 1: Compute default geometry quantum advantage
    # ---------------------------------------------------------------
    print("-" * 76)
    print("Step 1: Default geometry quantum advantage")
    print("-" * 76)
    t0 = time.time()
    qa_default, eff_q_default, eff_c_default = compute_quantum_advantage(
        sites=SITES, **DEFAULT_GEOMETRY
    )
    dt = time.time() - t0
    print(f"  Quantum efficiency:   {eff_q_default:.6f}")
    print(f"  Classical efficiency: {eff_c_default:.6f}")
    print(f"  Quantum advantage:    {qa_default:+.6f}")
    if eff_c_default > 1e-10:
        print(f"  Relative advantage:   {qa_default / eff_c_default * 100:+.2f}%")
    else:
        print(f"  Relative advantage:   N/A (classical ~0)")
    print(f"  Time: {dt:.2f} s")
    print(flush=True)

    # ---------------------------------------------------------------
    # Step 2: Run evolutionary search
    # ---------------------------------------------------------------
    print()
    print("-" * 76)
    print("Step 2: Differential Evolution search")
    print("-" * 76)
    print(flush=True)

    global _eval_count, _gen_best, _gen_best_params, _gen_count, _gen_start_eval
    _eval_count = 0
    _gen_best = -999.0
    _gen_best_params = None
    _gen_count = 0
    _gen_start_eval = 0

    t0_ga = time.time()
    result = differential_evolution(
        fitness_function,
        bounds=BOUNDS,
        maxiter=GA_MAXITER,
        popsize=GA_POPSIZE,
        seed=GA_SEED,
        callback=ga_callback,
        tol=1e-6,
        mutation=(0.5, 1.0),
        recombination=0.7,
        polish=False,
    )
    dt_ga = time.time() - t0_ga

    print()
    print(f"  GA completed in {dt_ga:.1f} s ({_eval_count} evaluations)")
    print(f"  DE result success: {result.success}")
    print(f"  DE result message: {result.message}")
    print()

    # Extract best geometry
    best_x = result.x
    best_qa = -result.fun  # negate back

    best_geometry = {}
    for name, val in zip(PARAM_NAMES, best_x):
        best_geometry[name] = val

    # Re-run best geometry to get full results
    print("-" * 76)
    print("Step 3: Verify best geometry")
    print("-" * 76)
    qa_best, eff_q_best, eff_c_best = compute_quantum_advantage(
        sites=SITES, **best_geometry
    )
    print(f"  Quantum efficiency:   {eff_q_best:.6f}")
    print(f"  Classical efficiency: {eff_c_best:.6f}")
    print(f"  Quantum advantage:    {qa_best:+.6f}")
    if eff_c_best > 1e-10:
        rel_best = qa_best / eff_c_best * 100
    else:
        rel_best = 0.0
    print(f"  Relative advantage:   {rel_best:+.2f}%")
    print()

    # ---------------------------------------------------------------
    # Step 4: Summary comparison
    # ---------------------------------------------------------------
    print("=" * 76)
    print("COMPARISON: DEFAULT vs OPTIMIZED GEOMETRY")
    print("=" * 76)
    print()
    if eff_c_default > 1e-10:
        rel_default = qa_default / eff_c_default * 100
    else:
        rel_default = 0.0

    print(f"  {'':25s} {'DEFAULT':>12s} {'OPTIMIZED':>12s} {'IMPROVEMENT':>12s}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12}")
    print(f"  {'Quantum efficiency':25s} {eff_q_default:12.6f} {eff_q_best:12.6f} {eff_q_best - eff_q_default:+12.6f}")
    print(f"  {'Classical efficiency':25s} {eff_c_default:12.6f} {eff_c_best:12.6f} {eff_c_best - eff_c_default:+12.6f}")
    print(f"  {'Quantum advantage':25s} {qa_default:+12.6f} {qa_best:+12.6f} {qa_best - qa_default:+12.6f}")
    print(f"  {'Relative advantage (%)':25s} {rel_default:+12.2f} {rel_best:+12.2f} {rel_best - rel_default:+12.2f}")
    print()
    print("  Optimal geometry parameters:")
    for name in PARAM_NAMES:
        default_val = DEFAULT_GEOMETRY[name]
        best_val = best_geometry[name]
        print(f"    {name:20s}: {default_val:8.2f} -> {best_val:8.2f}")
    print()

    # Amplification factor
    if abs(qa_default) > 1e-6:
        amplification = qa_best / qa_default
        print(f"  Quantum advantage amplification: {amplification:.1f}x")
    else:
        if qa_best > 1e-6:
            print(f"  Quantum advantage amplification: inf (default was ~0)")
        else:
            print(f"  Quantum advantage amplification: N/A (both ~0)")
    print()

    # ---------------------------------------------------------------
    # Step 5: Scale to 13 sites
    # ---------------------------------------------------------------
    print("=" * 76)
    print("SCALING TEST: Best geometry at 13 sites")
    print("=" * 76)
    print()

    t0 = time.time()
    qa_13, eff_q_13, eff_c_13 = compute_quantum_advantage(
        sites=13, **best_geometry
    )
    dt_13 = time.time() - t0

    if eff_c_13 > 1e-10:
        rel_13 = qa_13 / eff_c_13 * 100
    else:
        rel_13 = 0.0

    print(f"  Sites:                13")
    print(f"  Quantum efficiency:   {eff_q_13:.6f}")
    print(f"  Classical efficiency: {eff_c_13:.6f}")
    print(f"  Quantum advantage:    {qa_13:+.6f}")
    print(f"  Relative advantage:   {rel_13:+.2f}%")
    print(f"  Time: {dt_13:.2f} s")
    print()

    # Compare scaling
    print("  Scaling comparison:")
    print(f"    8 sites:  QA = {qa_best:+.6f}  ({rel_best:+.2f}%)")
    print(f"    13 sites: QA = {qa_13:+.6f}  ({rel_13:+.2f}%)")
    if abs(qa_best) > 1e-10:
        scaling_factor = qa_13 / qa_best
        print(f"    Scaling factor (13/8): {scaling_factor:.2f}x")
    print()

    # ---------------------------------------------------------------
    # Final verdict
    # ---------------------------------------------------------------
    print("=" * 76)
    print("FINAL VERDICT")
    print("=" * 76)
    print()

    if qa_best > 0.02:
        print("  STRONG QUANTUM ADVANTAGE FOUND")
        print(f"  The optimized geometry achieves {qa_best:+.6f} quantum advantage")
        print(f"  ({rel_best:+.2f}% relative), a substantial improvement over the")
        print(f"  default geometry's {qa_default:+.6f} ({rel_default:+.2f}%).")
    elif qa_best > 0.005:
        print("  MODERATE QUANTUM ADVANTAGE FOUND")
        print(f"  The optimized geometry achieves {qa_best:+.6f} quantum advantage")
        print(f"  ({rel_best:+.2f}% relative).")
    elif qa_best > 1e-4:
        print("  SMALL QUANTUM ADVANTAGE FOUND")
        print(f"  The optimized geometry achieves {qa_best:+.6f} quantum advantage")
        print(f"  ({rel_best:+.2f}% relative), but the effect is small.")
    else:
        print("  NO MEANINGFUL QUANTUM ADVANTAGE FOUND")
        print(f"  Even with optimized geometry, quantum advantage = {qa_best:+.6f}.")
        print(f"  The bath-derived Lindblad operators alone drive transport")
        print(f"  as well or better than adding the coherent Hamiltonian.")

    print()
    print("=" * 76)
    print("END OF PHASE 3 EVOLUTIONARY SEARCH")
    print("=" * 76)


if __name__ == "__main__":
    main()
