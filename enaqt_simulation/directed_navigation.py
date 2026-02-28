"""
Directed Navigation via Evolved Measurement-Basis Feedback
===========================================================

The definitive test: can evolution tune the measurement-basis-selection
feedback loop to navigate toward a specific target in conformation space?

This combines:
  - Level A (goal-directed navigation)
  - Level B (radical pair adaptive measurement)
  - The evolutionary argument

Model: Same radical pair (2 electrons + 1 nucleus, I=1, 12D Hilbert space) and
conformational feedback loop as measurement_basis_selection.py, but now:

  1. A FITNESS TARGET in conformation space.
  2. Evolvable feedback parameters (delta_S, delta_T, alpha, beta, gamma).
  3. Differential evolution to optimize those parameters.
  4. Comparison of four conditions:
       - Adaptive + evolved feedback
       - Fixed basis + evolved feedback (no adaptation)
       - Classical + evolved feedback (no quantum dynamics)
       - Adaptive + random feedback (no evolution)

Performance: P_S is precomputed on a 3D grid of (a_N, J, phi) values and
looked up via direct array indexing (nearest-neighbor). This replaces
expensive 144x144 matrix exponentials (~4ms each) with ~1us array lookups.
"""

import numpy as np
from scipy.optimize import differential_evolution
import time
import sys

# ---------------------------------------------------------------------------
# Import core operators from measurement_basis_selection
# ---------------------------------------------------------------------------
from enaqt_simulation.measurement_basis_selection import (
    build_operators,
    build_singlet_projector,
    compute_singlet_probability,
    theta_to_hamiltonian_params,
)

# ---------------------------------------------------------------------------
# Physical parameters (same as measurement_basis_selection.py)
# ---------------------------------------------------------------------------
B_FIELD = 50e-6      # T (Earth's field)
A_BASE  = 10.0       # MHz
J_BASE  = 0.0        # MHz
K_S     = 1.0        # us^-1
K_T     = 0.1        # us^-1
T2      = 1.0        # us
TAU     = 1.0        # us (radical pair lifetime per event)

# Fitness target in 6D conformation space
THETA_TARGET = np.array([3.0, -2.0, 1.5, -1.0, 2.0, -0.5])

# GA settings
N_EVENTS_GA    = 300   # events per trajectory during GA
N_SEEDS_GA     = 20    # seeds to average over during GA
GA_MAXITER     = 40
GA_POPSIZE     = 12
GA_SEED        = 42

# Comparison settings
N_EVENTS_COMP  = 300   # events per trajectory for comparison
N_RUNS_COMP    = 200   # runs per condition


# ---------------------------------------------------------------------------
# Precomputed P_S lookup table with direct array indexing
# ---------------------------------------------------------------------------
# We precompute P_S on a 3D grid and use direct array indexing for O(1) lookup.
# This avoids the overhead of scipy's RegularGridInterpolator.

GRID_N_AN  = 40    # grid points for a_N
GRID_N_J   = 30    # grid points for J
GRID_N_PHI = 25    # grid points for phi

# Ranges (generous, covering worst case)
AN_MIN, AN_MAX   = -500.0, 500.0    # MHz
J_MIN, J_MAX     = -300.0, 300.0    # MHz
PHI_MIN, PHI_MAX = -20.0, 20.0      # rad


class PSLookupTable:
    """Fast P_S lookup via precomputed 3D grid with nearest-neighbor indexing."""

    def __init__(self, ops, P_S):
        self.n_an = GRID_N_AN
        self.n_j = GRID_N_J
        self.n_phi = GRID_N_PHI

        self.an_min = AN_MIN
        self.an_max = AN_MAX
        self.j_min = J_MIN
        self.j_max = J_MAX
        self.phi_min = PHI_MIN
        self.phi_max = PHI_MAX

        # Precompute scale factors for index computation
        self.an_scale = (self.n_an - 1) / (AN_MAX - AN_MIN)
        self.j_scale = (self.n_j - 1) / (J_MAX - J_MIN)
        self.phi_scale = (self.n_phi - 1) / (PHI_MAX - PHI_MIN)

        # Build the grid
        total = self.n_an * self.n_j * self.n_phi
        print(f"    Computing {total} grid points...", flush=True)

        a_N_vals = np.linspace(AN_MIN, AN_MAX, self.n_an)
        J_vals = np.linspace(J_MIN, J_MAX, self.n_j)
        phi_vals = np.linspace(PHI_MIN, PHI_MAX, self.n_phi)

        self.grid = np.zeros((self.n_an, self.n_j, self.n_phi))
        computed = 0
        t0 = time.time()

        for i, a_N in enumerate(a_N_vals):
            for j, J in enumerate(J_vals):
                for k, phi in enumerate(phi_vals):
                    self.grid[i, j, k] = compute_singlet_probability(
                        ops, P_S, B_field=B_FIELD, a_N_MHz=a_N,
                        J_MHz=J, phi_rad=phi, k_S=K_S, k_T=K_T, T2=T2,
                        tau=TAU
                    )
                    computed += 1
            if (i + 1) % 10 == 0:
                elapsed = time.time() - t0
                rate = computed / elapsed
                remaining = (total - computed) / rate
                print(f"    {computed}/{total} ({computed/total*100:.0f}%) "
                      f"- {elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining",
                      flush=True)

        self.build_time = time.time() - t0
        print(f"    Grid complete in {self.build_time:.1f}s", flush=True)

    def lookup(self, a_N_MHz, J_MHz, phi_rad):
        """Fast nearest-neighbor lookup. Returns P_S."""
        # Clamp and compute indices
        a_N_c = min(max(a_N_MHz, self.an_min), self.an_max)
        J_c = min(max(J_MHz, self.j_min), self.j_max)
        phi_c = min(max(phi_rad, self.phi_min), self.phi_max)

        i = int(round((a_N_c - self.an_min) * self.an_scale))
        j = int(round((J_c - self.j_min) * self.j_scale))
        k = int(round((phi_c - self.phi_min) * self.phi_scale))

        # Clamp indices (safety)
        i = min(max(i, 0), self.n_an - 1)
        j = min(max(j, 0), self.n_j - 1)
        k = min(max(k, 0), self.n_phi - 1)

        return self.grid[i, j, k]


# ---------------------------------------------------------------------------
# Trajectory runners
# ---------------------------------------------------------------------------

def run_trajectory_adaptive(rng, ps_table, N_events, delta_S, delta_T,
                            alpha, beta, gamma_angle):
    """
    Adaptive basis: conformation feeds back into the Hamiltonian.
    Returns final theta (6D).
    """
    theta = np.zeros(6)
    a_base = A_BASE
    j_base = J_BASE

    for i in range(N_events):
        # Inline theta_to_hamiltonian_params for speed
        a_N = a_base + alpha * theta[0]
        J = j_base + beta * theta[1]
        phi = gamma_angle * theta[2]

        p_s = ps_table.lookup(a_N, J, phi)
        if rng.random() < p_s:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

    return theta


def run_trajectory_fixed_basis(rng, N_events, delta_S, delta_T, p_s_fixed):
    """
    Fixed basis: same delta_S/delta_T but alpha=beta=gamma=0.
    Returns final theta (6D).
    """
    theta = np.zeros(6)

    for i in range(N_events):
        if rng.random() < p_s_fixed:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

    return theta


def run_trajectory_classical(rng, N_events, delta_S, delta_T):
    """
    Classical: P_S = 0.5 coin flip.
    Returns final theta (6D).
    """
    theta = np.zeros(6)

    for i in range(N_events):
        if rng.random() < 0.5:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

    return theta


# ---------------------------------------------------------------------------
# Parameter encoding / decoding
# ---------------------------------------------------------------------------

def decode_params(x):
    """
    Decode the 15-parameter vector.

    x[0:6]   = delta_S
    x[6:12]  = delta_T
    x[12]    = alpha (hyperfine modulation, MHz)
    x[13]    = beta  (exchange modulation, MHz)
    x[14]    = gamma (field angle modulation, rad)
    """
    delta_S = x[0:6]
    delta_T = x[6:12]
    alpha = x[12]
    beta = x[13]
    gamma_angle = x[14]
    return delta_S, delta_T, alpha, beta, gamma_angle


# Parameter bounds
BOUNDS = (
    [(-0.3, 0.3)] * 6 +    # delta_S
    [(-0.3, 0.3)] * 6 +    # delta_T
    [(0.0, 5.0)] +          # alpha
    [(0.0, 3.0)] +          # beta
    [(0.0, 0.5)]            # gamma
)


# ---------------------------------------------------------------------------
# Fitness function
# ---------------------------------------------------------------------------

MIN_DELTA_SEPARATION = 0.05  # Minimum ||delta_S - delta_T|| to prevent trivial solutions


def fitness_function(x, ps_table):
    """
    Evaluate fitness: mean(||theta_final - target||^2) over N_SEEDS_GA seeds.
    Returns value to minimize.

    Includes a penalty for delta_S ~= delta_T (trivial solution where the
    measurement outcome doesn't matter because both shifts are identical).
    """
    delta_S, delta_T, alpha, beta, gamma_angle = decode_params(x)

    # Penalty for trivial solution: delta_S == delta_T means outcomes don't matter
    delta_diff = np.linalg.norm(delta_S - delta_T)
    if delta_diff < MIN_DELTA_SEPARATION:
        # Heavy penalty that increases as delta_S approaches delta_T
        return 1e6 * (1.0 + MIN_DELTA_SEPARATION - delta_diff)

    total_dist_sq = 0.0
    for seed_idx in range(N_SEEDS_GA):
        rng = np.random.default_rng(seed=1000 + seed_idx)
        theta_final = run_trajectory_adaptive(
            rng, ps_table, N_EVENTS_GA,
            delta_S, delta_T, alpha, beta, gamma_angle
        )
        total_dist_sq += np.sum((theta_final - THETA_TARGET) ** 2)

    return total_dist_sq / N_SEEDS_GA


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("  DIRECTED NAVIGATION VIA EVOLVED MEASUREMENT-BASIS FEEDBACK")
    print("  Combines Level A + Level B + Evolutionary Argument")
    print("=" * 78)

    print(f"\n--- Configuration ---")
    print(f"  Target: theta_target = {THETA_TARGET}")
    print(f"  Initial distance: ||theta_0 - theta_target|| = "
          f"{np.linalg.norm(THETA_TARGET):.4f}")
    print(f"  B_field     : {B_FIELD*1e6:.0f} uT")
    print(f"  a_base      : {A_BASE} MHz")
    print(f"  J_base      : {J_BASE} MHz")
    print(f"  k_S         : {K_S} us^-1")
    print(f"  k_T         : {K_T} us^-1")
    print(f"  T2          : {T2} us")
    print(f"  tau         : {TAU} us")
    print(f"  N_events GA : {N_EVENTS_GA}")
    print(f"  N_seeds GA  : {N_SEEDS_GA}")
    print(f"  GA maxiter  : {GA_MAXITER}")
    print(f"  GA popsize  : {GA_POPSIZE}")
    print(f"  N_events cmp: {N_EVENTS_COMP}")
    print(f"  N_runs cmp  : {N_RUNS_COMP}", flush=True)

    # Build operators
    print("\nBuilding spin operators...", flush=True)
    ops = build_operators()
    P_S = build_singlet_projector(ops)

    # Compute fixed-basis singlet probability (exact)
    p_s_fixed = compute_singlet_probability(
        ops, P_S, B_field=B_FIELD, a_N_MHz=A_BASE,
        J_MHz=J_BASE, phi_rad=0.0, k_S=K_S, k_T=K_T, T2=T2, tau=TAU
    )
    print(f"  P_S(fixed basis) = {p_s_fixed:.6f}", flush=True)

    initial_distance = np.linalg.norm(THETA_TARGET)

    # ===================================================================
    # PRECOMPUTE P_S LOOKUP TABLE
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PRECOMPUTING P_S LOOKUP TABLE")
    print(f"  Grid: {GRID_N_AN} x {GRID_N_J} x {GRID_N_PHI} = "
          f"{GRID_N_AN * GRID_N_J * GRID_N_PHI} points")
    print(f"  a_N range: [{AN_MIN}, {AN_MAX}] MHz")
    print(f"  J range:   [{J_MIN}, {J_MAX}] MHz")
    print(f"  phi range: [{PHI_MIN}, {PHI_MAX}] rad")
    print(f"{'='*78}", flush=True)

    ps_table = PSLookupTable(ops, P_S)

    # Verify lookup accuracy
    test_points = [
        (A_BASE, J_BASE, 0.0),
        (15.0, 1.0, 0.1),
        (5.0, -1.0, -0.1),
        (50.0, 10.0, 0.5),
    ]
    print(f"\n  Lookup accuracy check:")
    max_err = 0.0
    for a_N, J, phi in test_points:
        exact = compute_singlet_probability(
            ops, P_S, B_field=B_FIELD, a_N_MHz=a_N,
            J_MHz=J, phi_rad=phi, k_S=K_S, k_T=K_T, T2=T2, tau=TAU
        )
        approx = ps_table.lookup(a_N, J, phi)
        err = abs(exact - approx)
        max_err = max(max_err, err)
        print(f"    ({a_N:6.1f}, {J:5.1f}, {phi:5.2f}): "
              f"exact={exact:.6f}, lookup={approx:.6f}, err={err:.2e}")
    print(f"  Max lookup error: {max_err:.2e}")
    print(f"  Note: nearest-neighbor lookup; errors expected at coarse grid.",
          flush=True)

    # Quick benchmark
    t_bench = time.time()
    for _ in range(100000):
        ps_table.lookup(15.0, 1.0, 0.1)
    t_bench = time.time() - t_bench
    print(f"  Lookup speed: {t_bench/100000*1e6:.1f} us/lookup", flush=True)

    # ===================================================================
    # PHASE 1: EVOLUTIONARY OPTIMIZATION
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 1: EVOLUTIONARY OPTIMIZATION")
    print(f"  differential_evolution: maxiter={GA_MAXITER}, popsize={GA_POPSIZE}")
    print(f"  Each evaluation: {N_SEEDS_GA} seeds x {N_EVENTS_GA} events")
    print(f"{'='*78}\n", flush=True)

    generation_log = []
    gen_counter = [0]
    best_fun = [float('inf')]
    t_ga_start = time.time()

    def ga_callback(xk, convergence):
        gen_counter[0] += 1
        current_fun = fitness_function(xk, ps_table)
        if current_fun < best_fun[0]:
            best_fun[0] = current_fun
        mean_dist = np.sqrt(best_fun[0])
        elapsed = time.time() - t_ga_start
        generation_log.append({
            'gen': gen_counter[0],
            'mean_dist': mean_dist,
            'fitness': -best_fun[0],
            'elapsed': elapsed,
        })
        print(f"  Gen {gen_counter[0]:>3d} | Best dist~: {mean_dist:>8.4f} | "
              f"Fitness: {-best_fun[0]:>10.4f} | "
              f"Conv: {convergence:.4f} | "
              f"Elapsed: {elapsed:.1f}s", flush=True)

    result = differential_evolution(
        fitness_function,
        bounds=BOUNDS,
        args=(ps_table,),
        maxiter=GA_MAXITER,
        popsize=GA_POPSIZE,
        seed=GA_SEED,
        callback=ga_callback,
        tol=1e-6,
        mutation=(0.5, 1.0),
        recombination=0.7,
        polish=False,           # Skip L-BFGS-B polishing (slow with penalty)
        disp=False,
    )

    t_ga = time.time() - t_ga_start

    # Decode optimized parameters
    opt_delta_S, opt_delta_T, opt_alpha, opt_beta, opt_gamma = decode_params(
        result.x
    )

    print(f"\n--- GA Results ---")
    print(f"  Optimization time: {t_ga:.1f}s")
    print(f"  GA converged: {result.success}")
    print(f"  GA message: {result.message}")
    print(f"  Best mean dist^2: {result.fun:.4f}")
    print(f"  Best mean dist:   {np.sqrt(result.fun):.4f}")
    print(f"  Best fitness:     {-result.fun:.4f}")
    print(f"\n  Optimized parameters:")
    print(f"    delta_S = [{', '.join(f'{v:+.4f}' for v in opt_delta_S)}]")
    print(f"    delta_T = [{', '.join(f'{v:+.4f}' for v in opt_delta_T)}]")
    print(f"    alpha   = {opt_alpha:.4f} MHz")
    print(f"    beta    = {opt_beta:.4f} MHz")
    print(f"    gamma   = {opt_gamma:.4f} rad", flush=True)

    # ===================================================================
    # PHASE 2: COMPARISON OF FOUR CONDITIONS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 2: COMPARISON OF FOUR CONDITIONS")
    print(f"  {N_RUNS_COMP} runs x {N_EVENTS_COMP} events per condition")
    print(f"{'='*78}", flush=True)

    # Generate random (unevolved) feedback parameters for Condition 4
    rng_rand_params = np.random.default_rng(seed=999)
    rand_delta_S = rng_rand_params.uniform(-0.3, 0.3, size=6)
    rand_delta_T = rng_rand_params.uniform(-0.3, 0.3, size=6)

    conditions = {}

    # --- CONDITION 1: Adaptive + evolved ---
    print(f"\n  Condition 1: Adaptive + evolved feedback...", flush=True)
    t0 = time.time()
    finals_1 = np.zeros((N_RUNS_COMP, 6))
    for run in range(N_RUNS_COMP):
        if (run + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"    Run {run+1}/{N_RUNS_COMP} ({elapsed:.1f}s)", flush=True)
        rng = np.random.default_rng(seed=2000 + run)
        finals_1[run] = run_trajectory_adaptive(
            rng, ps_table, N_EVENTS_COMP,
            opt_delta_S, opt_delta_T, opt_alpha, opt_beta, opt_gamma
        )
    t1 = time.time() - t0
    conditions['Adaptive + evolved'] = finals_1
    print(f"    Done in {t1:.1f}s", flush=True)

    # --- CONDITION 2: Fixed basis + evolved ---
    print(f"\n  Condition 2: Fixed basis + evolved feedback...", flush=True)
    t0 = time.time()
    finals_2 = np.zeros((N_RUNS_COMP, 6))
    for run in range(N_RUNS_COMP):
        rng = np.random.default_rng(seed=2000 + run)
        finals_2[run] = run_trajectory_fixed_basis(
            rng, N_EVENTS_COMP,
            opt_delta_S, opt_delta_T, p_s_fixed
        )
    t2 = time.time() - t0
    conditions['Fixed basis + evolved'] = finals_2
    print(f"    Done in {t2:.1f}s", flush=True)

    # --- CONDITION 3: Classical + evolved ---
    print(f"\n  Condition 3: Classical + evolved feedback (P_S=0.5)...",
          flush=True)
    t0 = time.time()
    finals_3 = np.zeros((N_RUNS_COMP, 6))
    for run in range(N_RUNS_COMP):
        rng = np.random.default_rng(seed=2000 + run)
        finals_3[run] = run_trajectory_classical(
            rng, N_EVENTS_COMP,
            opt_delta_S, opt_delta_T
        )
    t3 = time.time() - t0
    conditions['Classical + evolved'] = finals_3
    print(f"    Done in {t3:.1f}s", flush=True)

    # --- CONDITION 4: Adaptive + random ---
    print(f"\n  Condition 4: Adaptive + random feedback...", flush=True)
    t0 = time.time()
    finals_4 = np.zeros((N_RUNS_COMP, 6))
    for run in range(N_RUNS_COMP):
        if (run + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"    Run {run+1}/{N_RUNS_COMP} ({elapsed:.1f}s)", flush=True)
        rng = np.random.default_rng(seed=2000 + run)
        finals_4[run] = run_trajectory_adaptive(
            rng, ps_table, N_EVENTS_COMP,
            rand_delta_S, rand_delta_T, opt_alpha, opt_beta, opt_gamma
        )
    t4 = time.time() - t0
    conditions['Adaptive + random'] = finals_4
    print(f"    Done in {t4:.1f}s", flush=True)

    # ===================================================================
    # PHASE 3: METRICS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 3: METRICS AND COMPARISON")
    print(f"{'='*78}")

    threshold = 0.20 * initial_distance

    print(f"\n  Target: {THETA_TARGET}")
    print(f"  Initial distance: {initial_distance:.4f}")
    print(f"  Hitting threshold (20% of initial): {threshold:.4f}")

    results_table = {}

    for name, finals in conditions.items():
        dists = np.linalg.norm(finals - THETA_TARGET, axis=1)
        mean_dist = np.mean(dists)
        std_dist = np.std(dists)
        hitting_rate = np.mean(dists < threshold)
        mean_fitness = np.mean(-(dists ** 2))

        results_table[name] = {
            'mean_dist': mean_dist,
            'std_dist': std_dist,
            'hitting_rate': hitting_rate,
            'mean_fitness': mean_fitness,
        }

    # Print comparison table
    print(f"\n  {'Condition':<25s} | {'Mean dist':>10s} | {'Std':>8s} | "
          f"{'Hit rate':>9s} | {'Mean fitness':>13s}")
    print(f"  {'-'*25}-+-{'-'*10}-+-{'-'*8}-+-{'-'*9}-+-{'-'*13}")

    for name in ['Adaptive + evolved', 'Fixed basis + evolved',
                 'Classical + evolved', 'Adaptive + random']:
        r = results_table[name]
        print(f"  {name:<25s} | {r['mean_dist']:>10.4f} | {r['std_dist']:>8.4f} | "
              f"{r['hitting_rate']:>9.1%} | {r['mean_fitness']:>13.4f}")

    # ===================================================================
    # PHASE 4: STATISTICAL SIGNIFICANCE
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 4: STATISTICAL SIGNIFICANCE")
    print(f"{'='*78}")

    from scipy import stats

    dists_1 = np.linalg.norm(finals_1 - THETA_TARGET, axis=1)
    dists_2 = np.linalg.norm(finals_2 - THETA_TARGET, axis=1)
    dists_3 = np.linalg.norm(finals_3 - THETA_TARGET, axis=1)
    dists_4 = np.linalg.norm(finals_4 - THETA_TARGET, axis=1)

    comparisons = [
        ("Adaptive+evolved vs Fixed+evolved", dists_1, dists_2),
        ("Adaptive+evolved vs Classical+evolved", dists_1, dists_3),
        ("Adaptive+evolved vs Adaptive+random", dists_1, dists_4),
        ("Fixed+evolved vs Classical+evolved", dists_2, dists_3),
    ]

    print(f"\n  Two-sample t-tests on distance to target:")
    for label, d_a, d_b in comparisons:
        t_stat, p_val = stats.ttest_ind(d_a, d_b)
        pooled_std = np.sqrt((np.std(d_a)**2 + np.std(d_b)**2) / 2)
        cohens_d = (np.mean(d_a) - np.mean(d_b)) / pooled_std if pooled_std > 1e-12 else 0.0
        print(f"    {label}")
        print(f"      t = {t_stat:+.4f}, p = {p_val:.2e}, Cohen's d = {cohens_d:+.4f}")

    # Mann-Whitney U tests (non-parametric)
    print(f"\n  Mann-Whitney U tests on distance to target:")
    for label, d_a, d_b in comparisons:
        u_stat, p_val = stats.mannwhitneyu(d_a, d_b, alternative='two-sided')
        print(f"    {label}")
        print(f"      U = {u_stat:.1f}, p = {p_val:.2e}")

    # ===================================================================
    # PHASE 5: DETAILED ANALYSIS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 5: DETAILED ANALYSIS")
    print(f"{'='*78}")

    # Mean final theta for each condition
    print(f"\n  Mean final theta vectors:")
    for name, finals in conditions.items():
        mean_theta = np.mean(finals, axis=0)
        print(f"    {name:<25s}: [{', '.join(f'{v:+.4f}' for v in mean_theta)}]")
    print(f"    {'Target':<25s}: [{', '.join(f'{v:+.4f}' for v in THETA_TARGET)}]")

    # Per-dimension analysis
    print(f"\n  Per-dimension mean error (mean_theta - target):")
    print(f"    {'Dim':>4s}  {'Target':>7s}  {'Adpt+Evo':>9s}  {'Fix+Evo':>9s}  "
          f"{'Cls+Evo':>9s}  {'Adpt+Rnd':>9s}")
    for d in range(6):
        t_val = THETA_TARGET[d]
        m1 = np.mean(finals_1[:, d]) - t_val
        m2 = np.mean(finals_2[:, d]) - t_val
        m3 = np.mean(finals_3[:, d]) - t_val
        m4 = np.mean(finals_4[:, d]) - t_val
        print(f"    {d:>4d}  {t_val:>+7.2f}  {m1:>+9.4f}  {m2:>+9.4f}  "
              f"{m3:>+9.4f}  {m4:>+9.4f}")

    # Fraction closer than each condition
    print(f"\n  Pairwise proximity comparison (fraction of runs where "
          f"Adaptive+evolved is closer to target):")
    for name, finals in [('Fixed basis + evolved', finals_2),
                         ('Classical + evolved', finals_3),
                         ('Adaptive + random', finals_4)]:
        d_evo = np.linalg.norm(finals_1 - THETA_TARGET, axis=1)
        d_other = np.linalg.norm(finals - THETA_TARGET, axis=1)
        frac_closer = np.mean(d_evo < d_other)
        print(f"    vs {name:<25s}: {frac_closer:.1%} of runs")

    # GA convergence summary
    if generation_log:
        print(f"\n  GA convergence summary:")
        print(f"    {'Gen':>4s}  {'Mean dist':>10s}  {'Fitness':>10s}  {'Elapsed':>8s}")
        for entry in generation_log:
            print(f"    {entry['gen']:>4d}  {entry['mean_dist']:>10.4f}  "
                  f"{entry['fitness']:>10.4f}  {entry['elapsed']:>7.1f}s")

    # ===================================================================
    # VERDICT
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  VERDICT")
    print(f"{'='*78}")

    r1 = results_table['Adaptive + evolved']
    r2 = results_table['Fixed basis + evolved']
    r3 = results_table['Classical + evolved']
    r4 = results_table['Adaptive + random']

    adaptive_best = (r1['mean_dist'] < r2['mean_dist'] and
                     r1['mean_dist'] < r3['mean_dist'] and
                     r1['mean_dist'] < r4['mean_dist'])

    t_12, p_12 = stats.ttest_ind(dists_1, dists_2)
    t_13, p_13 = stats.ttest_ind(dists_1, dists_3)
    t_14, p_14 = stats.ttest_ind(dists_1, dists_4)

    sig_vs_fixed = p_12 < 0.05 and r1['mean_dist'] < r2['mean_dist']
    sig_vs_classical = p_13 < 0.05 and r1['mean_dist'] < r3['mean_dist']
    sig_vs_random = p_14 < 0.05 and r1['mean_dist'] < r4['mean_dist']

    print(f"\n  Distance improvement (lower = better):")
    print(f"    Initial distance to target:     {initial_distance:.4f}")
    print(f"    Adaptive + evolved:             {r1['mean_dist']:.4f} "
          f"({(1 - r1['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Fixed basis + evolved:          {r2['mean_dist']:.4f} "
          f"({(1 - r2['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Classical + evolved:            {r3['mean_dist']:.4f} "
          f"({(1 - r3['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Adaptive + random:              {r4['mean_dist']:.4f} "
          f"({(1 - r4['mean_dist']/initial_distance)*100:+.1f}%)")

    print(f"\n  Significance (Adaptive+evolved vs each):")
    print(f"    vs Fixed basis:  p = {p_12:.2e}  "
          f"{'SIGNIFICANT' if sig_vs_fixed else 'not significant'}")
    print(f"    vs Classical:    p = {p_13:.2e}  "
          f"{'SIGNIFICANT' if sig_vs_classical else 'not significant'}")
    print(f"    vs Random fbk:  p = {p_14:.2e}  "
          f"{'SIGNIFICANT' if sig_vs_random else 'not significant'}")

    if adaptive_best and sig_vs_fixed and sig_vs_classical and sig_vs_random:
        print(f"\n  >>> STRONG POSITIVE RESULT <<<")
        print(f"  Evolution CAN tune the adaptive measurement-basis feedback loop")
        print(f"  for directed navigation toward a specific target.")
        print(f"  Adaptive + evolved is SIGNIFICANTLY closer to target than ALL")
        print(f"  three control conditions.")
        print(f"\n  This means:")
        print(f"    1. Adaptive measurement (choosing which questions to ask) matters")
        print(f"       -- fixed basis with same feedback is worse.")
        print(f"    2. Quantum dynamics matter -- classical coin flip is worse.")
        print(f"    3. Evolutionary tuning matters -- random feedback is worse.")
        print(f"  ALL THREE components (adaptation + quantum + evolution) contribute")
        print(f"  to goal-directed navigation in conformation space.")
    elif adaptive_best and (sig_vs_fixed or sig_vs_classical or sig_vs_random):
        print(f"\n  >>> PARTIAL POSITIVE RESULT <<<")
        print(f"  Adaptive + evolved achieves the BEST mean distance to target,")
        print(f"  with significant advantage over at least one control condition.")
        factors = []
        if sig_vs_fixed:
            factors.append("measurement-basis adaptation")
        if sig_vs_classical:
            factors.append("quantum dynamics")
        if sig_vs_random:
            factors.append("evolutionary parameter tuning")
        print(f"  Significant factors: {', '.join(factors)}")
        if not sig_vs_fixed:
            print(f"  Note: Fixed basis performs comparably, suggesting the evolved")
            print(f"  shift vectors alone may be sufficient without adaptive feedback.")
        if not sig_vs_classical:
            print(f"  Note: Classical performs comparably, suggesting quantum dynamics")
            print(f"  may not be critical for this navigation task.")
        if not sig_vs_random:
            print(f"  Note: Random feedback performs comparably, suggesting the adaptive")
            print(f"  loop alone provides most of the benefit.")
    else:
        print(f"\n  >>> NEGATIVE OR INCONCLUSIVE RESULT <<<")
        print(f"  Adaptive + evolved does NOT clearly outperform all controls.")
        if r2['mean_dist'] <= r1['mean_dist']:
            print(f"  Fixed basis matches/beats adaptive, suggesting adaptation is")
            print(f"  not necessary -- evolved shift vectors alone suffice.")
        if r3['mean_dist'] <= r1['mean_dist']:
            print(f"  Classical matches/beats adaptive, suggesting quantum dynamics")
            print(f"  are not needed for this type of navigation.")
        if r4['mean_dist'] <= r1['mean_dist']:
            print(f"  Random feedback matches/beats evolved, suggesting evolution")
            print(f"  does not improve navigation performance.")

    print(f"\n{'='*78}\n")


if __name__ == "__main__":
    main()
