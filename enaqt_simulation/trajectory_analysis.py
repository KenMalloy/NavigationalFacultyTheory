"""
Trajectory analysis: comparing the JOURNEY of quantum vs classical evolution
through state space.

Previous simulations showed quantum and classical systems reach approximately
the same steady state (~0.18% difference in transport efficiency). But NFT
claims the quantum advantage is in NAVIGATION -- the path through state space,
not the destination.

This script tests whether quantum and classical TRAJECTORIES are measurably
different during transient dynamics, even if they converge.

Uses the same secular Redfield Lindblad approach as quantum_vs_classical.py.
"""

from __future__ import annotations

import sys
import time

import numpy as np
from scipy.linalg import eigh, svdvals

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    rad_ps_to_cm,
    KB_OVER_HBAR_PS_K,
)
from enaqt_simulation.quantum_vs_classical import derive_lindblad_operators


# -----------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------

SITES = 8
COUPLING_CM = 60.0
DISORDER_CM = 25.0
SEED = 7
HELIX_RADIUS_NM = 2.0
HELIX_RISE_NM = 0.8
HELIX_TWIST_DEG = 27.7
DIPOLE_TILT_DEG = 20.0

BATH_STRENGTH_CM = 35.0
CUTOFF_CM = 53.0
TEMPERATURE_K = 310.0

SINK_SITE = 7
SINK_RATE_CM = 1.0
SOURCE_SITE = 0

T_MAX_PS = 50.0
N_TIME_POINTS = 1000

# Perturbation test parameters
PERTURBATION_TIME_PS = 1.0
PERTURBATION_SITE = 3
PERTURBATION_STRENGTH = 0.01


# -----------------------------------------------------------------------
# Trajectory metrics
# -----------------------------------------------------------------------

def trace_distance(rho_q, rho_c):
    """D(rho_Q, rho_C) = 0.5 * ||rho_Q - rho_C||_1 (sum of singular values)."""
    diff = rho_q - rho_c
    return 0.5 * np.sum(svdvals(diff))


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho), computed from eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return -np.sum(evals * np.log(evals))


def purity(rho):
    """gamma(rho) = Tr(rho^2)."""
    return np.real(np.trace(rho @ rho))


def off_diagonal_coherence(rho):
    """C(rho) = sum_{i != j} |rho_{ij}|."""
    n = rho.shape[0]
    total = 0.0
    for i in range(n):
        for j in range(n):
            if i != j:
                total += abs(rho[i, j])
    return total


def site_population_variance(rho):
    """Var(p) = Var({rho_ii}) across sites."""
    diag = np.real(np.diag(rho))
    return np.var(diag)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    import qutip

    print("=" * 78)
    print("TRAJECTORY ANALYSIS: Quantum vs Classical Journey Through State Space")
    print("=" * 78)
    print()

    # -------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------

    sink_rate = cm_to_rad_ps(SINK_RATE_CM)
    cutoff_rad_ps = cm_to_rad_ps(CUTOFF_CM)
    kT_rad_ps = KB_OVER_HBAR_PS_K * TEMPERATURE_K
    bath_strength_rad_ps = cm_to_rad_ps(BATH_STRENGTH_CM)

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

    H = model.hamiltonian  # in rad/ps
    N = SITES
    N_total = N + 1  # +1 for trap site

    print("Parameters:")
    print(f"  sites                   : {SITES}")
    print(f"  coupling_cm             : {COUPLING_CM}")
    print(f"  disorder_cm             : {DISORDER_CM}")
    print(f"  seed                    : {SEED}")
    print(f"  bath_strength_cm        : {BATH_STRENGTH_CM}")
    print(f"  cutoff_cm               : {CUTOFF_CM}")
    print(f"  temperature_K           : {TEMPERATURE_K}")
    print(f"  sink_rate_cm            : {SINK_RATE_CM}")
    print(f"  T_max (ps)              : {T_MAX_PS}")
    print(f"  n_time_points           : {N_TIME_POINTS}")
    print(f"  model                   : {model.label}")
    print()

    # Derive Lindblad operators (same as quantum_vs_classical.py)
    print("Deriving Lindblad operators from full Hamiltonian...")
    t0 = time.time()
    collapse_ops, eigvals, eigvecs = derive_lindblad_operators(
        H_chromophore=H,
        bath_strength_rad_ps=bath_strength_rad_ps,
        cutoff_rad_ps=cutoff_rad_ps,
        kT_rad_ps=kT_rad_ps,
        sink_site=SINK_SITE,
        sink_rate_ps_inv=sink_rate,
    )
    dt = time.time() - t0
    print(f"  Number of collapse operators: {len(collapse_ops)}")
    print(f"  Time to derive: {dt:.3f} s")
    print()

    # Initial state: |0><0| in extended Hilbert space
    psi0 = qutip.basis(N_total, SOURCE_SITE)

    # Time list with fine resolution
    tlist = np.linspace(0, T_MAX_PS, N_TIME_POINTS)

    # -------------------------------------------------------------------
    # Run quantum evolution (full H + collapse operators)
    # -------------------------------------------------------------------

    print("Running QUANTUM evolution (full H + bath + sink)...")
    H_ext_q = np.zeros((N_total, N_total), dtype=complex)
    H_ext_q[:N, :N] = H
    H_qobj_q = qutip.Qobj(H_ext_q)

    t0 = time.time()
    result_q = qutip.mesolve(H_qobj_q, psi0, tlist, c_ops=collapse_ops)
    dt_q = time.time() - t0
    print(f"  Done in {dt_q:.2f} s")

    # -------------------------------------------------------------------
    # Run classical evolution (H=0 + same collapse operators)
    # -------------------------------------------------------------------

    print("Running CLASSICAL evolution (H=0 + same bath + sink)...")
    H_ext_c = np.zeros((N_total, N_total), dtype=complex)
    H_qobj_c = qutip.Qobj(H_ext_c)

    t0 = time.time()
    result_c = qutip.mesolve(H_qobj_c, psi0, tlist, c_ops=collapse_ops)
    dt_c = time.time() - t0
    print(f"  Done in {dt_c:.2f} s")
    print()

    # -------------------------------------------------------------------
    # Compute trajectory metrics at every time step
    # -------------------------------------------------------------------

    print("Computing trajectory metrics at all time steps...")
    t0 = time.time()

    n_steps = len(tlist)
    trace_dists = np.zeros(n_steps)
    entropy_q = np.zeros(n_steps)
    entropy_c = np.zeros(n_steps)
    delta_entropy = np.zeros(n_steps)
    purity_q = np.zeros(n_steps)
    purity_c = np.zeros(n_steps)
    coherence_q = np.zeros(n_steps)
    coherence_c = np.zeros(n_steps)
    pop_var_q = np.zeros(n_steps)
    pop_var_c = np.zeros(n_steps)

    for i in range(n_steps):
        rho_q_full = result_q.states[i].full()
        rho_c_full = result_c.states[i].full()

        trace_dists[i] = trace_distance(rho_q_full, rho_c_full)
        entropy_q[i] = von_neumann_entropy(rho_q_full)
        entropy_c[i] = von_neumann_entropy(rho_c_full)
        delta_entropy[i] = entropy_q[i] - entropy_c[i]
        purity_q[i] = purity(rho_q_full)
        purity_c[i] = purity(rho_c_full)
        coherence_q[i] = off_diagonal_coherence(rho_q_full)
        coherence_c[i] = off_diagonal_coherence(rho_c_full)
        pop_var_q[i] = site_population_variance(rho_q_full)
        pop_var_c[i] = site_population_variance(rho_c_full)

    dt_metrics = time.time() - t0
    print(f"  Done in {dt_metrics:.2f} s")
    print()

    # -------------------------------------------------------------------
    # Summary table at selected time points
    # -------------------------------------------------------------------

    report_times = [0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]

    print("=" * 78)
    print("TRAJECTORY METRICS AT SELECTED TIME POINTS")
    print("=" * 78)
    print()

    header = (
        f"{'t(ps)':>7} | {'TraceDist':>10} | {'S_q':>8} {'S_c':>8} {'dS':>8} |"
        f" {'Pur_q':>8} {'Pur_c':>8} | {'Coh_q':>8} {'Coh_c':>8} |"
        f" {'Var_q':>10} {'Var_c':>10}"
    )
    print(header)
    print("-" * len(header))

    for t_report in report_times:
        idx = int(np.argmin(np.abs(tlist - t_report)))
        t_actual = tlist[idx]
        print(
            f"{t_actual:7.3f} | {trace_dists[idx]:10.6f} |"
            f" {entropy_q[idx]:8.5f} {entropy_c[idx]:8.5f} {delta_entropy[idx]:8.5f} |"
            f" {purity_q[idx]:8.5f} {purity_c[idx]:8.5f} |"
            f" {coherence_q[idx]:8.5f} {coherence_c[idx]:8.5f} |"
            f" {pop_var_q[idx]:10.7f} {pop_var_c[idx]:10.7f}"
        )

    print()

    # -------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------

    print("=" * 78)
    print("TRAJECTORY ANALYSIS")
    print("=" * 78)
    print()

    # 1. Peak divergence
    peak_idx = int(np.argmax(trace_dists))
    peak_trace_dist = trace_dists[peak_idx]
    peak_time = tlist[peak_idx]
    print(f"1. PEAK DIVERGENCE:")
    print(f"   Maximum trace distance:  {peak_trace_dist:.6f}")
    print(f"   Occurs at time:          {peak_time:.4f} ps")
    print()

    # 2. Exploration advantage (time-averaged delta-S)
    # Early transient: 0 to 5 ps
    early_mask = tlist <= 5.0
    delta_s_early = np.mean(delta_entropy[early_mask])
    # Middle: 5 to 10 ps
    middle_mask = (tlist >= 5.0) & (tlist <= 10.0)
    delta_s_middle = np.mean(delta_entropy[middle_mask])
    # Full: 0 to 50 ps
    delta_s_full = np.mean(delta_entropy)

    print(f"2. EXPLORATION ADVANTAGE (time-averaged Delta-S = S_quantum - S_classical):")
    print(f"   Early transient (0-5 ps):   {delta_s_early:+.6f}")
    print(f"   Middle (5-10 ps):           {delta_s_middle:+.6f}")
    print(f"   Full evolution (0-50 ps):   {delta_s_full:+.6f}")
    if delta_s_early > 0:
        print(f"   --> Quantum explores MORE of state space early on (wider entropy)")
    elif delta_s_early < 0:
        print(f"   --> Classical explores MORE of state space early on")
    else:
        print(f"   --> No exploration difference")
    print()

    # 3. Transient coherence window
    peak_coherence_q = np.max(coherence_q)
    threshold_coherence = 0.01 * peak_coherence_q
    # Find last time coherence is above threshold
    above_threshold = np.where(coherence_q >= threshold_coherence)[0]
    if len(above_threshold) > 0:
        coherence_window_end = tlist[above_threshold[-1]]
    else:
        coherence_window_end = 0.0

    # Also find where classical coherence is significant (it should be ~0)
    peak_coherence_c = np.max(coherence_c)

    print(f"3. TRANSIENT COHERENCE WINDOW:")
    print(f"   Peak quantum coherence:     {peak_coherence_q:.6f}")
    print(f"   Peak classical coherence:   {peak_coherence_c:.6f}")
    print(f"   1% threshold:               {threshold_coherence:.6f}")
    print(f"   Coherence window duration:  {coherence_window_end:.4f} ps")
    print(f"   (time until quantum coherence drops below 1% of peak)")
    print()

    # 4. Convergence time: when trace distance drops to 10% of peak
    threshold_convergence = 0.10 * peak_trace_dist
    # Look for when trace distance drops below threshold AFTER the peak
    convergence_found = False
    convergence_time = T_MAX_PS
    for i in range(peak_idx, n_steps):
        if trace_dists[i] < threshold_convergence:
            convergence_time = tlist[i]
            convergence_found = True
            break

    print(f"4. CONVERGENCE TIME:")
    print(f"   10% threshold:              {threshold_convergence:.6f}")
    if convergence_found:
        print(f"   Convergence time:           {convergence_time:.4f} ps")
    else:
        print(f"   Trajectories have NOT converged by {T_MAX_PS} ps")
        print(f"   Final trace distance:       {trace_dists[-1]:.6f}")
    print()

    # 5. Integrated trajectory divergence
    dt_step = tlist[1] - tlist[0]
    integrated_divergence = np.trapz(trace_dists, tlist)

    print(f"5. INTEGRATED TRAJECTORY DIVERGENCE:")
    print(f"   integral_0^T D(t) dt =      {integrated_divergence:.6f} ps")
    print(f"   (cumulative quantum journey distance)")
    print()

    # -------------------------------------------------------------------
    # Perturbation sensitivity test
    # -------------------------------------------------------------------

    print("=" * 78)
    print("PERTURBATION SENSITIVITY TEST")
    print("=" * 78)
    print()
    print(f"   Perturbation: add {PERTURBATION_STRENGTH} * |{PERTURBATION_SITE}><{PERTURBATION_SITE}| at t = {PERTURBATION_TIME_PS} ps")
    print(f"   Then continue evolving and compare perturbed vs unperturbed")
    print()

    # Find the index closest to perturbation time
    perturb_idx = int(np.argmin(np.abs(tlist - PERTURBATION_TIME_PS)))
    t_perturb_actual = tlist[perturb_idx]
    print(f"   Actual perturbation time: {t_perturb_actual:.4f} ps (index {perturb_idx})")

    # Get the states at perturbation time
    rho_q_at_perturb = result_q.states[perturb_idx]
    rho_c_at_perturb = result_c.states[perturb_idx]

    # Create perturbation operator
    perturb_op = np.zeros((N_total, N_total), dtype=complex)
    perturb_op[PERTURBATION_SITE, PERTURBATION_SITE] = PERTURBATION_STRENGTH
    perturb_qobj = qutip.Qobj(perturb_op)

    # Perturb quantum state
    rho_q_perturbed = rho_q_at_perturb + perturb_qobj
    # Renormalize
    tr_q = rho_q_perturbed.tr()
    rho_q_perturbed = rho_q_perturbed / tr_q

    # Perturb classical state
    rho_c_perturbed = rho_c_at_perturb + perturb_qobj
    tr_c = rho_c_perturbed.tr()
    rho_c_perturbed = rho_c_perturbed / tr_c

    # Time list for post-perturbation evolution
    tlist_post = tlist[perturb_idx:] - tlist[perturb_idx]

    # Evolve perturbed quantum
    print("   Running perturbed quantum evolution...")
    t0 = time.time()
    result_q_perturbed = qutip.mesolve(
        H_qobj_q, rho_q_perturbed, tlist_post, c_ops=collapse_ops
    )
    dt_qp = time.time() - t0
    print(f"   Done in {dt_qp:.2f} s")

    # Evolve perturbed classical
    print("   Running perturbed classical evolution...")
    t0 = time.time()
    result_c_perturbed = qutip.mesolve(
        H_qobj_c, rho_c_perturbed, tlist_post, c_ops=collapse_ops
    )
    dt_cp = time.time() - t0
    print(f"   Done in {dt_cp:.2f} s")
    print()

    # Compute perturbation propagation
    n_post = len(tlist_post)
    perturb_dist_q = np.zeros(n_post)
    perturb_dist_c = np.zeros(n_post)

    for i in range(n_post):
        # Unperturbed states (from original evolution, offset by perturb_idx)
        rho_q_unp = result_q.states[perturb_idx + i].full()
        rho_c_unp = result_c.states[perturb_idx + i].full()
        # Perturbed states
        rho_q_p = result_q_perturbed.states[i].full()
        rho_c_p = result_c_perturbed.states[i].full()

        perturb_dist_q[i] = trace_distance(rho_q_p, rho_q_unp)
        perturb_dist_c[i] = trace_distance(rho_c_p, rho_c_unp)

    # Report perturbation results
    tlist_post_abs = tlist[perturb_idx:]

    print("   Perturbation propagation (trace distance between perturbed and unperturbed):")
    print()
    perturb_report_times = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    print(f"   {'t_rel(ps)':>10} {'t_abs(ps)':>10} | {'D_quantum':>10} {'D_classical':>12} {'Ratio(Q/C)':>11}")
    print(f"   {'-'*60}")
    for t_rel in perturb_report_times:
        if t_rel > tlist_post[-1]:
            break
        idx_rel = int(np.argmin(np.abs(tlist_post - t_rel)))
        t_abs = tlist_post_abs[idx_rel]
        dq = perturb_dist_q[idx_rel]
        dc = perturb_dist_c[idx_rel]
        ratio = dq / dc if dc > 1e-15 else float('inf')
        print(f"   {tlist_post[idx_rel]:10.4f} {t_abs:10.4f} | {dq:10.6f} {dc:12.6f} {ratio:11.4f}")

    # Peak perturbation response
    peak_perturb_q = np.max(perturb_dist_q)
    peak_perturb_c = np.max(perturb_dist_c)
    peak_perturb_q_idx = int(np.argmax(perturb_dist_q))
    peak_perturb_c_idx = int(np.argmax(perturb_dist_c))

    # Integrated perturbation sensitivity
    integrated_perturb_q = np.trapz(perturb_dist_q, tlist_post)
    integrated_perturb_c = np.trapz(perturb_dist_c, tlist_post)

    print()
    print(f"   Peak perturbation response (quantum):    {peak_perturb_q:.6f} at t_rel={tlist_post[peak_perturb_q_idx]:.4f} ps")
    print(f"   Peak perturbation response (classical):  {peak_perturb_c:.6f} at t_rel={tlist_post[peak_perturb_c_idx]:.4f} ps")
    print(f"   Integrated perturbation (quantum):       {integrated_perturb_q:.6f} ps")
    print(f"   Integrated perturbation (classical):     {integrated_perturb_c:.6f} ps")
    if integrated_perturb_c > 1e-15:
        print(f"   Sensitivity ratio (Q/C):                 {integrated_perturb_q / integrated_perturb_c:.4f}")
    print()

    # -------------------------------------------------------------------
    # Final verdict
    # -------------------------------------------------------------------

    print("=" * 78)
    print("VERDICT: Are quantum and classical TRAJECTORIES measurably different?")
    print("=" * 78)
    print()

    # Evaluate key findings
    findings = []

    # Peak trace distance assessment
    if peak_trace_dist > 0.1:
        findings.append(f"STRONG trajectory divergence: peak trace distance = {peak_trace_dist:.4f} (>{'>'}0.1)")
    elif peak_trace_dist > 0.01:
        findings.append(f"MODERATE trajectory divergence: peak trace distance = {peak_trace_dist:.4f}")
    else:
        findings.append(f"WEAK trajectory divergence: peak trace distance = {peak_trace_dist:.4f}")

    # Coherence window assessment
    if coherence_window_end > 10.0:
        findings.append(f"LONG coherence window: {coherence_window_end:.2f} ps (quantum effects persist)")
    elif coherence_window_end > 1.0:
        findings.append(f"MODERATE coherence window: {coherence_window_end:.2f} ps")
    else:
        findings.append(f"SHORT coherence window: {coherence_window_end:.2f} ps (quantum effects decay quickly)")

    # Exploration advantage
    if abs(delta_s_early) > 0.01:
        if delta_s_early > 0:
            findings.append(f"Quantum explores MORE state space early (Delta-S = {delta_s_early:+.4f})")
        else:
            findings.append(f"Classical explores MORE state space early (Delta-S = {delta_s_early:+.4f})")
    else:
        findings.append(f"Similar exploration breadth (Delta-S = {delta_s_early:+.4f})")

    # Integrated divergence
    findings.append(f"Integrated trajectory divergence: {integrated_divergence:.4f} ps")

    # Convergence assessment
    if convergence_found:
        findings.append(f"Trajectories converge at {convergence_time:.2f} ps")
    else:
        findings.append(f"Trajectories have NOT converged by {T_MAX_PS} ps")

    # Perturbation sensitivity
    if integrated_perturb_c > 1e-15:
        sensitivity_ratio = integrated_perturb_q / integrated_perturb_c
        if sensitivity_ratio > 1.5:
            findings.append(f"Quantum is {sensitivity_ratio:.2f}x MORE sensitive to perturbation")
        elif sensitivity_ratio < 0.67:
            findings.append(f"Classical is {1.0/sensitivity_ratio:.2f}x MORE sensitive to perturbation")
        else:
            findings.append(f"Similar perturbation sensitivity (ratio = {sensitivity_ratio:.2f})")

    for i, finding in enumerate(findings):
        print(f"  {i+1}. {finding}")
    print()

    # Overall verdict
    journey_different = (
        peak_trace_dist > 0.01
        or abs(delta_s_early) > 0.005
        or coherence_window_end > 1.0
        or integrated_divergence > 0.1
    )

    if journey_different:
        print("  OVERALL: YES -- Quantum and classical trajectories are measurably")
        print("  different during transient dynamics, even though they converge to")
        print("  similar final states. The JOURNEY through state space differs, even")
        print("  if the DESTINATION is approximately the same.")
        print()
        print("  This supports the NFT claim that quantum advantage lies in NAVIGATION")
        print("  (how the system explores state space during transients) rather than")
        print("  in the final steady-state efficiency.")
    else:
        print("  OVERALL: NO -- Quantum and classical trajectories are NOT measurably")
        print("  different. The journey through state space is essentially identical,")
        print("  matching the finding that steady-state efficiency is also nearly")
        print("  identical. The Hamiltonian has negligible effect on both the")
        print("  trajectory and the destination at this bath strength.")

    print()
    print("=" * 78)
    print("END OF TRAJECTORY ANALYSIS")
    print("=" * 78)


if __name__ == "__main__":
    main()
