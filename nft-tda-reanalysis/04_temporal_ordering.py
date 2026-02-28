"""
Step 4: The actual NFT test — temporal ordering analysis.

CORE PREDICTION (XIII.B / XIII.H):
  During the transition from consciousness to unconsciousness,
  topological complexity declines BEFORE classical metrics.
  During emergence, topological complexity recovers AFTER classical metrics.

METHOD:
  1. For each subject, extract the induction transition window
  2. Compute running classical and topological metrics in sliding windows
  3. Detect "onset of decline" for each metric via change-point analysis
  4. Test whether topological onset precedes classical onset
  5. Same analysis in reverse for emergence

STATISTICS:
  - Within-subject paired comparisons of onset times
  - Group-level: Wilcoxon signed-rank test on onset latencies
  - Effect size: rank-biserial correlation
  - Bootstrap CIs on the median onset difference

This is the analysis that, if the temporal ordering holds,
constitutes a novel finding no prior TDA-on-EEG paper has tested.
"""
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    RESULTS_DIR, FIGURES_DIR,
    N_BOOTSTRAP, ONSET_THRESHOLD_PERCENTILE,
)


# ========== ONSET DETECTION ==========

def detect_onset(timeseries: np.ndarray, baseline_end: int,
                 direction: str = "decrease") -> int | None:
    """
    Detect the onset of significant change from baseline.

    Args:
        timeseries: metric values over time (epochs)
        baseline_end: index of last baseline epoch
        direction: "decrease" for induction, "increase" for emergence

    Returns:
        onset index, or None if no significant change detected
    """
    baseline = timeseries[:baseline_end]
    mu = np.mean(baseline)
    sigma = np.std(baseline)

    if sigma < 1e-10:
        return None

    # Threshold: 2 SD from baseline mean
    if direction == "decrease":
        threshold = mu - 2 * sigma
        # First epoch after baseline that stays below threshold
        # for at least 3 consecutive epochs (robustness)
        post = timeseries[baseline_end:]
        consecutive = 0
        for i, val in enumerate(post):
            if val < threshold:
                consecutive += 1
                if consecutive >= 3:
                    return baseline_end + i - 2  # onset of the run
            else:
                consecutive = 0
    else:  # increase
        threshold = mu + 2 * sigma
        post = timeseries[baseline_end:]
        consecutive = 0
        for i, val in enumerate(post):
            if val > threshold:
                consecutive += 1
                if consecutive >= 3:
                    return baseline_end + i - 2
            else:
                consecutive = 0

    return None  # no onset detected


def bootstrap_onset_difference(topo_onsets: np.ndarray,
                                classical_onsets: np.ndarray,
                                n_boot: int = N_BOOTSTRAP) -> dict:
    """
    Bootstrap CI on the difference (classical_onset - topo_onset).
    Positive values = topology drops first (NFT prediction).
    """
    diffs = classical_onsets - topo_onsets  # positive = topo first
    observed_median = np.median(diffs)

    boot_medians = []
    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        boot_medians.append(np.median(sample))

    boot_medians = np.array(boot_medians)
    ci_low = np.percentile(boot_medians, 2.5)
    ci_high = np.percentile(boot_medians, 97.5)

    return {
        "median_diff": observed_median,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_topo_first": np.mean(boot_medians > 0),  # proportion supporting NFT
        "boot_medians": boot_medians,
    }


# ========== MAIN ANALYSIS ==========

def analyze_temporal_ordering(df: pd.DataFrame) -> dict:
    """
    Main analysis: compare onset times of topological vs. classical
    metric decline during induction.
    """
    # --- Define metric groups ---
    topo_metrics = [c for c in df.columns if c.startswith(("betti_", "persistence_entropy_", "topo_complexity"))]
    classical_metrics = [c for c in df.columns if c.startswith(("power_", "sef95", "rms", "wpli_", "lempel_ziv"))]

    # Use the composite scores for the primary analysis
    primary_topo = "topo_complexity"  # sum of persistence entropies
    primary_classical = [
        "power_total",
        "rms",
        "lempel_ziv",
        "wpli_alpha",
    ]

    results = {
        "subjects": [],
        "topo_onsets": [],
        "classical_onsets": {},  # per classical metric
    }

    for cm in primary_classical:
        results["classical_onsets"][cm] = []

    subjects = df["subject"].unique()

    for subject in subjects:
        sdf = df[df["subject"] == subject].sort_values("epoch_idx").reset_index()

        if primary_topo not in sdf.columns:
            print(f"  {subject}: missing {primary_topo}, skipping")
            continue

        # Determine baseline period
        # Use first 20% of epochs as baseline (awake)
        # This is approximate — refine based on actual event markers
        n_epochs = len(sdf)
        baseline_end = max(int(n_epochs * 0.2), 5)

        # Detect topological onset
        topo_ts = sdf[primary_topo].values
        topo_onset = detect_onset(topo_ts, baseline_end, direction="decrease")

        if topo_onset is None:
            print(f"  {subject}: no topological onset detected, skipping")
            continue

        results["subjects"].append(subject)
        results["topo_onsets"].append(topo_onset)

        # Detect classical onsets
        for cm in primary_classical:
            if cm not in sdf.columns:
                results["classical_onsets"][cm].append(np.nan)
                continue
            cl_ts = sdf[cm].values
            cl_onset = detect_onset(cl_ts, baseline_end, direction="decrease")
            results["classical_onsets"][cm].append(
                cl_onset if cl_onset is not None else np.nan
            )

    return results


def run_statistics(results: dict) -> pd.DataFrame:
    """
    Statistical tests on temporal ordering.
    """
    topo = np.array(results["topo_onsets"], dtype=float)
    stats_rows = []

    for cm, onsets in results["classical_onsets"].items():
        classical = np.array(onsets, dtype=float)

        # Drop subjects where either onset is missing
        mask = ~(np.isnan(topo) | np.isnan(classical))
        t = topo[mask]
        c = classical[mask]

        if len(t) < 5:
            print(f"  {cm}: too few valid pairs ({len(t)}), skipping")
            continue

        # Difference: positive = topology drops first
        diff = c - t

        # Wilcoxon signed-rank test
        stat, p_val = stats.wilcoxon(diff, alternative="greater")
        # alternative="greater" tests H1: diff > 0 (topo drops first)

        # Effect size: rank-biserial correlation
        n = len(diff)
        r = 1 - (2 * stat) / (n * (n + 1))

        # Bootstrap
        boot = bootstrap_onset_difference(t, c)

        stats_rows.append({
            "classical_metric": cm,
            "n_subjects": len(t),
            "median_diff_epochs": boot["median_diff"],
            "ci_low": boot["ci_low"],
            "ci_high": boot["ci_high"],
            "wilcoxon_stat": stat,
            "p_value": p_val,
            "effect_size_r": r,
            "prop_topo_first": np.mean(diff > 0),
            "nft_supported": boot["ci_low"] > 0,  # entire CI > 0
        })

    return pd.DataFrame(stats_rows)


# ========== PLOTTING ==========

def plot_temporal_ordering(df: pd.DataFrame, results: dict,
                           subject: str = None):
    """
    Plot time courses of topological and classical metrics
    for a single subject (or first subject if none specified).
    """
    if subject is None:
        subject = results["subjects"][0]

    sdf = df[df["subject"] == subject].sort_values("epoch_idx")

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Normalize all metrics to [0, 1] for visual comparison
    def norm(x):
        xmin, xmax = np.nanmin(x), np.nanmax(x)
        if xmax - xmin < 1e-10:
            return x * 0
        return (x - xmin) / (xmax - xmin)

    epochs = sdf["epoch_idx"].values

    # Panel 1: Topological metrics
    ax = axes[0]
    ax.set_title(f"Topological Metrics — {subject}", fontsize=12)
    for col in ["topo_complexity", "betti_1_max", "persistence_entropy_1"]:
        if col in sdf.columns:
            ax.plot(epochs, norm(sdf[col].values), label=col, alpha=0.8)
    ax.set_ylabel("Normalized value")
    ax.legend(fontsize=8)
    ax.axhline(0.5, color="gray", ls="--", alpha=0.3)

    # Panel 2: Classical metrics
    ax = axes[1]
    ax.set_title("Classical Metrics", fontsize=12)
    for col in ["power_total", "rms", "lempel_ziv", "wpli_alpha"]:
        if col in sdf.columns:
            ax.plot(epochs, norm(sdf[col].values), label=col, alpha=0.8)
    ax.set_ylabel("Normalized value")
    ax.legend(fontsize=8)
    ax.axhline(0.5, color="gray", ls="--", alpha=0.3)

    # Panel 3: Direct comparison of composite scores
    ax = axes[2]
    ax.set_title("Topological vs. Classical Composite (NFT test)", fontsize=12)
    if "topo_complexity" in sdf.columns:
        ax.plot(epochs, norm(sdf["topo_complexity"].values),
                label="Topological complexity", color="tab:red", lw=2)
    if "lempel_ziv" in sdf.columns:
        ax.plot(epochs, norm(sdf["lempel_ziv"].values),
                label="Lempel-Ziv complexity", color="tab:blue", lw=2)
    ax.set_ylabel("Normalized value")
    ax.set_xlabel("Epoch index (time →)")
    ax.legend(fontsize=10)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / f"temporal_ordering_{subject}.png", dpi=150)
    plt.close()
    print(f"  Saved figure: temporal_ordering_{subject}.png")


def plot_group_results(stats_df: pd.DataFrame, results: dict):
    """Plot group-level onset difference distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Onset differences per classical metric
    ax = axes[0]
    for _, row in stats_df.iterrows():
        ax.barh(
            row["classical_metric"],
            row["median_diff_epochs"],
            xerr=[[row["median_diff_epochs"] - row["ci_low"]],
                   [row["ci_high"] - row["median_diff_epochs"]]],
            color="tab:red" if row["nft_supported"] else "tab:gray",
            alpha=0.7,
        )
    ax.axvline(0, color="black", ls="-", lw=1)
    ax.set_xlabel("Onset difference (epochs)\n← classical first | topology first →")
    ax.set_title("Temporal Ordering: Topo vs. Classical Onset")

    # Panel 2: Per-subject scatter for primary comparison
    ax = axes[1]
    topo = np.array(results["topo_onsets"])
    classical = np.array(results["classical_onsets"].get("lempel_ziv", []))
    mask = ~np.isnan(classical)
    if mask.sum() > 0:
        ax.scatter(topo[mask], classical[mask], alpha=0.6, s=60)
        lims = [0, max(np.max(topo[mask]), np.max(classical[mask])) * 1.1]
        ax.plot(lims, lims, "k--", alpha=0.4, label="simultaneous")
        ax.set_xlabel("Topological onset (epoch)")
        ax.set_ylabel("Classical onset (epoch)")
        ax.set_title("Per-Subject Onset Comparison")
        ax.legend()

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "group_temporal_ordering.png", dpi=150)
    plt.close()
    print("  Saved figure: group_temporal_ordering.png")


# ========== MAIN ==========

def main():
    combined_path = RESULTS_DIR / "all_subjects_metrics.csv"
    if not combined_path.exists():
        print("No metrics file found. Run 03_compute_metrics.py first.")
        return

    df = pd.read_csv(combined_path)
    print(f"Loaded {len(df)} epochs from {df['subject'].nunique()} subjects.\n")

    # --- Temporal ordering analysis ---
    print("Running temporal ordering analysis...")
    results = analyze_temporal_ordering(df)
    print(f"  Valid subjects: {len(results['subjects'])}\n")

    if len(results["subjects"]) < 3:
        print("Too few subjects with detected onsets for group statistics.")
        print("Check preprocessing and event labeling.")
        return

    # --- Statistics ---
    print("Computing statistics...")
    stats_df = run_statistics(results)
    stats_df.to_csv(RESULTS_DIR / "temporal_ordering_stats.csv", index=False)
    print(f"\n{'='*60}")
    print("RESULTS: Temporal Ordering Test")
    print(f"{'='*60}")
    print(stats_df.to_string(index=False))
    print(f"\n{'='*60}")

    # Interpretation
    n_supported = stats_df["nft_supported"].sum()
    n_total = len(stats_df)
    print(f"\nNFT prediction supported (CI entirely > 0): "
          f"{n_supported}/{n_total} classical metrics")

    if n_supported == n_total:
        print("→ STRONG SUPPORT: Topology drops before ALL classical metrics.")
    elif n_supported > 0:
        print("→ PARTIAL SUPPORT: Topology drops before SOME classical metrics.")
    else:
        print("→ NOT SUPPORTED: No evidence for temporal ordering.")
        print("  (This is a legitimate negative result — report it.)")

    # --- Figures ---
    print("\nGenerating figures...")
    for subject in results["subjects"][:3]:  # plot first 3 subjects
        plot_temporal_ordering(df, results, subject)
    plot_group_results(stats_df, results)

    print("\nDone. Check figures/ and results/ directories.")
    print("\nNext: write the paper describing this analysis.")


if __name__ == "__main__":
    main()
