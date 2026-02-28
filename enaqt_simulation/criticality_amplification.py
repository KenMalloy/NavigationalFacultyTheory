"""
Criticality Amplification Simulation
=====================================
Tests whether operating at criticality amplifies a tiny quantum bias
(~0.18% from microtubule ENAQT) into macroscopic behavioral differences.

Model: Branching neural network with N=1000 neurons on a random directed graph.
The branching ratio sigma = p * k_avg controls the criticality regime.
At sigma=1 (critical), susceptibility diverges and small perturbations
cascade through power-law avalanches.
"""

import numpy as np


def build_network(N, k_avg, rng):
    """Build a random directed graph with N neurons and average out-degree k_avg."""
    # For each neuron, sample k_avg downstream targets (with replacement allowed)
    adjacency = [[] for _ in range(N)]
    for i in range(N):
        n_targets = rng.poisson(k_avg)
        if n_targets > 0:
            targets = rng.choice(N, size=n_targets, replace=False) if n_targets <= N else rng.choice(N, size=n_targets, replace=True)
            # Remove self-connections
            targets = targets[targets != i]
            adjacency[i] = targets.tolist()
    return adjacency


def run_avalanche(adjacency, N, p, epsilon, rng):
    """
    Run a single avalanche starting from one random seed neuron.

    Parameters
    ----------
    adjacency : list of lists
        Directed graph adjacency list.
    N : int
        Number of neurons.
    p : float
        Base firing probability per connection.
    epsilon : float
        Quantum bias added to firing probability.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    int
        Avalanche size (total number of neurons that fired).
    """
    # Pick a random seed neuron
    seed_neuron = rng.integers(0, N)
    active = {seed_neuron}
    fired = {seed_neuron}
    p_eff = min(p + epsilon, 1.0)

    while active:
        next_active = set()
        for neuron in active:
            for target in adjacency[neuron]:
                if target not in fired:
                    if rng.random() < p_eff:
                        next_active.add(target)
                        fired.add(target)
        active = next_active

    return len(fired)


def run_avalanche_ensemble(adjacency, N, p, epsilon, n_avalanches, rng):
    """Run an ensemble of avalanches and collect size statistics."""
    sizes = np.zeros(n_avalanches, dtype=int)
    for i in range(n_avalanches):
        sizes[i] = run_avalanche(adjacency, N, p, epsilon, rng)
    return sizes


def compute_stats(sizes, N):
    """Compute summary statistics for avalanche size distribution."""
    return {
        "mean": np.mean(sizes),
        "median": np.median(sizes),
        "max": np.max(sizes),
        "p_large": np.mean(sizes > 100),  # P(size > 100)
        "std": np.std(sizes),
    }


def main():
    # -------------------------------------------------------------------------
    # Parameters
    # -------------------------------------------------------------------------
    N = 1000
    k_avg = 3
    n_avalanches = 10_000
    epsilon = 0.002  # quantum bias (~0.18%)
    seed = 42

    sigma_values = [0.9, 0.95, 0.99, 1.0, 1.01, 1.05]

    print("=" * 80)
    print("CRITICALITY AMPLIFICATION SIMULATION")
    print("=" * 80)
    print(f"  N = {N} neurons, k_avg = {k_avg}")
    print(f"  Avalanches per condition: {n_avalanches}")
    print(f"  Quantum bias epsilon = {epsilon}")
    print(f"  Random seed = {seed}")
    print()

    # Build network (shared across all runs for fair comparison)
    rng_net = np.random.default_rng(seed)
    adjacency = build_network(N, k_avg, rng_net)

    # Compute actual average out-degree
    actual_k = np.mean([len(adj) for adj in adjacency])
    print(f"  Actual mean out-degree: {actual_k:.3f}")
    print()

    # -------------------------------------------------------------------------
    # Part 1: Criticality sweep
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("PART 1: AVALANCHE STATISTICS ACROSS CRITICALITY REGIMES")
    print("=" * 80)
    print()

    results = {}

    for sigma in sigma_values:
        p = sigma / actual_k  # branching parameter

        print(f"--- sigma = {sigma:.2f} (p = {p:.6f}) ---")

        # Without quantum bias
        rng_no_bias = np.random.default_rng(seed + int(sigma * 100))
        sizes_no_bias = run_avalanche_ensemble(adjacency, N, p, 0.0, n_avalanches, rng_no_bias)
        stats_no_bias = compute_stats(sizes_no_bias, N)

        # With quantum bias
        rng_bias = np.random.default_rng(seed + int(sigma * 100))
        sizes_bias = run_avalanche_ensemble(adjacency, N, p, epsilon, n_avalanches, rng_bias)
        stats_bias = compute_stats(sizes_bias, N)

        # Amplification factor
        if stats_no_bias["mean"] > 0:
            amp_factor = (stats_bias["mean"] - stats_no_bias["mean"]) / stats_no_bias["mean"]
        else:
            amp_factor = float("inf")

        results[sigma] = {
            "stats_no_bias": stats_no_bias,
            "stats_bias": stats_bias,
            "amplification": amp_factor,
        }

        print(f"  WITHOUT bias:")
        print(f"    Mean size:    {stats_no_bias['mean']:.2f} +/- {stats_no_bias['std']:.2f}")
        print(f"    Median size:  {stats_no_bias['median']:.1f}")
        print(f"    Max size:     {stats_no_bias['max']}")
        print(f"    P(size>100):  {stats_no_bias['p_large']:.4f}")
        print()
        print(f"  WITH bias (epsilon={epsilon}):")
        print(f"    Mean size:    {stats_bias['mean']:.2f} +/- {stats_bias['std']:.2f}")
        print(f"    Median size:  {stats_bias['median']:.1f}")
        print(f"    Max size:     {stats_bias['max']}")
        print(f"    P(size>100):  {stats_bias['p_large']:.4f}")
        print()
        print(f"  AMPLIFICATION FACTOR: {amp_factor:+.4f} ({amp_factor * 100:+.2f}%)")
        print()

    # Summary table
    print("=" * 80)
    print("AMPLIFICATION SUMMARY")
    print("=" * 80)
    print(f"{'sigma':>8} | {'Mean (no bias)':>14} | {'Mean (bias)':>12} | {'Amp Factor':>12} | {'P(>100) no bias':>16} | {'P(>100) bias':>13}")
    print("-" * 90)
    for sigma in sigma_values:
        r = results[sigma]
        print(
            f"{sigma:8.2f} | "
            f"{r['stats_no_bias']['mean']:14.2f} | "
            f"{r['stats_bias']['mean']:12.2f} | "
            f"{r['amplification']:+12.4f} | "
            f"{r['stats_no_bias']['p_large']:16.4f} | "
            f"{r['stats_bias']['p_large']:13.4f}"
        )
    print()

    # -------------------------------------------------------------------------
    # Part 2: Bias scaling at criticality
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("PART 2: AMPLIFICATION vs BIAS STRENGTH AT CRITICALITY (sigma=1.0)")
    print("=" * 80)
    print()

    sigma_crit = 1.0
    p_crit = sigma_crit / actual_k
    epsilon_values = [0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]

    # Baseline without bias
    rng_baseline = np.random.default_rng(seed + 1000)
    sizes_baseline = run_avalanche_ensemble(adjacency, N, p_crit, 0.0, n_avalanches, rng_baseline)
    stats_baseline = compute_stats(sizes_baseline, N)

    print(f"Baseline (no bias): mean = {stats_baseline['mean']:.2f}, median = {stats_baseline['median']:.1f}")
    print()

    print(f"{'epsilon':>10} | {'Mean size':>10} | {'Amp Factor':>12} | {'Amp/epsilon':>12} | {'P(>100)':>10}")
    print("-" * 65)

    amp_factors = []
    for eps in epsilon_values:
        rng_eps = np.random.default_rng(seed + 1000)
        sizes_eps = run_avalanche_ensemble(adjacency, N, p_crit, eps, n_avalanches, rng_eps)
        stats_eps = compute_stats(sizes_eps, N)

        amp = (stats_eps["mean"] - stats_baseline["mean"]) / stats_baseline["mean"]
        amp_per_eps = amp / eps if eps > 0 else 0
        amp_factors.append((eps, amp, amp_per_eps))

        print(
            f"{eps:10.4f} | "
            f"{stats_eps['mean']:10.2f} | "
            f"{amp:+12.4f} | "
            f"{amp_per_eps:12.2f} | "
            f"{stats_eps['p_large']:10.4f}"
        )

    print()

    # Check if amplification grows faster than linearly
    # If amp/epsilon increases with epsilon, the response is superlinear
    print("Scaling analysis:")
    print("  If Amp/epsilon INCREASES with epsilon => superlinear (divergent) response")
    print("  If Amp/epsilon is CONSTANT => linear response")
    print("  If Amp/epsilon DECREASES with epsilon => sublinear (saturating) response")
    print()

    first_ratio = amp_factors[0][2]
    last_ratio = amp_factors[-1][2]
    if last_ratio > first_ratio * 1.5:
        scaling = "SUPERLINEAR (divergent)"
    elif last_ratio < first_ratio * 0.67:
        scaling = "SUBLINEAR (saturating)"
    else:
        scaling = "APPROXIMATELY LINEAR"
    print(f"  Amp/epsilon at smallest bias: {first_ratio:.2f}")
    print(f"  Amp/epsilon at largest bias:  {last_ratio:.2f}")
    print(f"  Scaling behavior: {scaling}")
    print()

    # -------------------------------------------------------------------------
    # Part 3: Verdict
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    # Find amplification at critical vs subcritical
    amp_subcrit = results[0.9]["amplification"]
    amp_crit = results[1.0]["amplification"]
    amp_supercrit = results[1.05]["amplification"]

    print(f"  Amplification at sigma=0.90 (subcritical):  {amp_subcrit:+.4f} ({amp_subcrit * 100:+.2f}%)")
    print(f"  Amplification at sigma=1.00 (critical):     {amp_crit:+.4f} ({amp_crit * 100:+.2f}%)")
    print(f"  Amplification at sigma=1.05 (supercritical): {amp_supercrit:+.4f} ({amp_supercrit * 100:+.2f}%)")
    print()

    ratio_crit_to_subcrit = abs(amp_crit / amp_subcrit) if amp_subcrit != 0 else float("inf")
    print(f"  Ratio (critical / subcritical amplification): {ratio_crit_to_subcrit:.1f}x")
    print()

    if ratio_crit_to_subcrit > 2.0:
        print("  RESULT: YES - Criticality AMPLIFIES the quantum bias.")
        print(f"  The {epsilon * 100:.1f}% quantum perturbation produces {ratio_crit_to_subcrit:.1f}x")
        print("  larger relative effect at criticality compared to subcritical regime.")
        print()
        print("  INTERPRETATION: If neural dynamics operate near criticality (as")
        print("  substantial evidence suggests), then even the tiny 0.18% probability")
        print("  bias from quantum effects in microtubules could be amplified into")
        print("  macroscopically detectable differences in neural avalanche statistics.")
    else:
        print("  RESULT: The amplification at criticality is not substantially")
        print("  larger than at subcritical regimes for this network size.")
        print("  Larger networks or finer tuning to the critical point may be needed.")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
