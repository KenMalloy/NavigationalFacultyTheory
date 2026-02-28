"""
Step 4: Acquisition-ordered temporal ordering analysis.

DS005620 does not include induction markers inside the rest recordings, so this
script implements an honest proxy analysis:

1. Use awake eyes-closed epochs as the subject-specific baseline.
2. Concatenate sed/sed2 rest epochs in acquisition-time order.
3. Detect the earliest sustained deviation from baseline for topological and
   classical metrics.
4. Test whether topological metrics cross threshold earlier than classical ones.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from config import (
    RESULTS_DIR,
    FIGURES_DIR,
    AWAKE_BASELINE_ACQ,
    POST_BASELINE_TASKS,
    N_BOOTSTRAP,
    ONSET_THRESHOLD_PERCENTILE,
    ONSET_MIN_CONSECUTIVE,
)


# ========== DATA PREPARATION ==========

def build_subject_series(df: pd.DataFrame, subject: str) -> pd.DataFrame | None:
    """
    Build an acquisition-ordered epoch series for one subject.

    Baseline = awake / eyes-closed epochs.
    Post-baseline = sed and sed2 rest epochs ordered by scans.tsv acquisition time.
    """
    sdf = df[df["subject"] == subject].copy()
    if sdf.empty:
        return None

    sdf["acq_time_dt"] = pd.to_datetime(sdf["acq_time"], utc=True, errors="coerce")
    baseline = sdf[
        (sdf["task"] == "awake")
        & (sdf["acquisition"] == AWAKE_BASELINE_ACQ)
    ].sort_values(["acq_time_dt", "epoch_idx"])
    post = sdf[
        (sdf["task"].isin(POST_BASELINE_TASKS))
        & (sdf["acquisition"] == "rest")
    ].sort_values(["acq_time_dt", "epoch_idx"])

    if baseline.empty or post.empty:
        return None

    series = pd.concat([baseline, post], ignore_index=True)
    series["ordered_epoch_idx"] = np.arange(len(series))
    series["phase"] = np.where(series.index < len(baseline), "baseline", "post")
    return series


# ========== ONSET DETECTION ==========

def detect_onset(
    timeseries: np.ndarray,
    baseline_end: int,
    direction: str = "decrease",
    threshold_percentile: float = ONSET_THRESHOLD_PERCENTILE,
    min_consecutive: int = ONSET_MIN_CONSECUTIVE,
) -> int | None:
    """
    Detect onset of sustained change relative to the baseline distribution.
    """
    baseline = np.asarray(timeseries[:baseline_end], dtype=float)
    post = np.asarray(timeseries[baseline_end:], dtype=float)

    if len(baseline) < min_consecutive or len(post) < min_consecutive:
        return None

    if direction == "decrease":
        threshold = np.percentile(baseline, 100 - threshold_percentile)
        comparator = lambda value: value <= threshold
    else:
        threshold = np.percentile(baseline, threshold_percentile)
        comparator = lambda value: value >= threshold

    consecutive = 0
    for i, value in enumerate(post):
        if comparator(value):
            consecutive += 1
            if consecutive >= min_consecutive:
                return baseline_end + i - min_consecutive + 1
        else:
            consecutive = 0
    return None


def bootstrap_onset_difference(
    topo_onsets: np.ndarray,
    classical_onsets: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
) -> dict:
    """
    Bootstrap the median difference (classical - topo).
    Positive values mean topology changes first.
    """
    diffs = classical_onsets - topo_onsets
    observed_median = float(np.median(diffs))

    rng = np.random.default_rng(42)
    boot_medians = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        boot_medians[i] = np.median(sample)

    return {
        "median_diff": observed_median,
        "ci_low": float(np.percentile(boot_medians, 2.5)),
        "ci_high": float(np.percentile(boot_medians, 97.5)),
        "p_topo_first": float(np.mean(boot_medians > 0)),
        "boot_medians": boot_medians,
    }


# ========== ANALYSIS ==========

def analyze_temporal_ordering(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Compare the onset of topological decline against classical metrics.
    """
    primary_topo = "topo_complexity"
    primary_classical = ["power_total", "rms", "lempel_ziv", "wpli_alpha"]

    results = {
        "subjects": [],
        "topo_onsets": [],
        "classical_onsets": {metric: [] for metric in primary_classical},
    }
    onset_rows: list[dict] = []

    for subject in sorted(df["subject"].unique()):
        series = build_subject_series(df, subject)
        if series is None:
            print(f"  {subject}: missing awake EC baseline or rest recordings, skipping")
            continue

        baseline_end = int((series["phase"] == "baseline").sum())
        topo_onset = detect_onset(series[primary_topo].to_numpy(), baseline_end, direction="decrease")
        if topo_onset is None:
            print(f"  {subject}: no topological onset detected, skipping")
            continue

        row = {"subject": subject, "topo_onset": topo_onset}
        results["subjects"].append(subject)
        results["topo_onsets"].append(topo_onset)

        for metric in primary_classical:
            if metric not in series.columns:
                onset = np.nan
            else:
                detected = detect_onset(series[metric].to_numpy(), baseline_end, direction="decrease")
                onset = detected if detected is not None else np.nan
            results["classical_onsets"][metric].append(onset)
            row[f"{metric}_onset"] = onset

        onset_rows.append(row)

    return results, pd.DataFrame(onset_rows)


def _rank_biserial(diff: np.ndarray) -> float:
    nonzero = diff[diff != 0]
    n = len(nonzero)
    if n == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(nonzero))
    positive = np.sum(ranks[nonzero > 0])
    negative = np.sum(ranks[nonzero < 0])
    return float((positive - negative) / (n * (n + 1) / 2))


def run_statistics(results: dict) -> pd.DataFrame:
    topo = np.asarray(results["topo_onsets"], dtype=float)
    stats_rows: list[dict] = []

    for metric, onsets in results["classical_onsets"].items():
        classical = np.asarray(onsets, dtype=float)
        valid = ~(np.isnan(topo) | np.isnan(classical))
        topo_valid = topo[valid]
        classical_valid = classical[valid]

        if len(topo_valid) < 5:
            print(f"  {metric}: too few valid pairs ({len(topo_valid)}), skipping")
            continue

        diff = classical_valid - topo_valid

        if np.allclose(diff, 0.0):
            stat = 0.0
            p_value = 1.0
        else:
            stat, p_value = stats.wilcoxon(diff, alternative="greater")

        boot = bootstrap_onset_difference(topo_valid, classical_valid)

        stats_rows.append(
            {
                "classical_metric": metric,
                "n_subjects": int(len(diff)),
                "median_diff_epochs": boot["median_diff"],
                "ci_low": boot["ci_low"],
                "ci_high": boot["ci_high"],
                "wilcoxon_stat": float(stat),
                "p_value": float(p_value),
                "effect_size_r": _rank_biserial(diff),
                "prop_topo_first": float(np.mean(diff > 0)),
                "nft_supported": bool(boot["ci_low"] > 0),
            }
        )

    return pd.DataFrame(stats_rows)


# ========== PLOTTING ==========

def _normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return values
    vmin = np.nanmin(values)
    vmax = np.nanmax(values)
    if not np.isfinite(vmin) or not np.isfinite(vmax) or abs(vmax - vmin) < 1e-10:
        return np.zeros_like(values)
    return (values - vmin) / (vmax - vmin)


def plot_temporal_ordering(df: pd.DataFrame, results: dict, subject: str | None = None):
    """
    Plot one subject's acquisition-ordered baseline/rest epoch trajectory.
    """
    if subject is None:
        subject = results["subjects"][0]

    series = build_subject_series(df, subject)
    if series is None:
        return

    epochs = series["ordered_epoch_idx"].to_numpy()
    boundaries = series.groupby("bids_stem")["ordered_epoch_idx"].min().sort_values()

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    ax = axes[0]
    ax.set_title(f"Topological Metrics — {subject}", fontsize=12)
    for column in ("topo_complexity", "betti_1_max", "persistence_entropy_1"):
        if column in series.columns:
            ax.plot(epochs, _normalize(series[column].to_numpy()), label=column, alpha=0.85)
    ax.set_ylabel("Normalized value")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.set_title("Classical Metrics", fontsize=12)
    for column in ("power_total", "rms", "lempel_ziv", "wpli_alpha"):
        if column in series.columns:
            ax.plot(epochs, _normalize(series[column].to_numpy()), label=column, alpha=0.85)
    ax.set_ylabel("Normalized value")
    ax.legend(fontsize=8)

    ax = axes[2]
    ax.set_title("Primary Comparison: Topology vs. Lempel-Ziv", fontsize=12)
    ax.plot(
        epochs,
        _normalize(series["topo_complexity"].to_numpy()),
        label="topo_complexity",
        color="tab:red",
        lw=2,
    )
    if "lempel_ziv" in series.columns:
        ax.plot(
            epochs,
            _normalize(series["lempel_ziv"].to_numpy()),
            label="lempel_ziv",
            color="tab:blue",
            lw=2,
        )
    ax.set_ylabel("Normalized value")
    ax.set_xlabel("Ordered epoch index")
    ax.legend(fontsize=10)

    for axis in axes:
        for _, start in boundaries.items():
            axis.axvline(start, color="gray", linestyle="--", alpha=0.2)

    plt.tight_layout()
    out_path = FIGURES_DIR / f"temporal_ordering_{subject}.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved figure: {out_path.name}")


def plot_group_results(stats_df: pd.DataFrame, results: dict):
    """Plot group-level onset differences and the primary onset scatter."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    for _, row in stats_df.iterrows():
        ax.barh(
            row["classical_metric"],
            row["median_diff_epochs"],
            xerr=[
                [row["median_diff_epochs"] - row["ci_low"]],
                [row["ci_high"] - row["median_diff_epochs"]],
            ],
            color="tab:red" if row["nft_supported"] else "tab:gray",
            alpha=0.75,
        )
    ax.axvline(0, color="black", lw=1)
    ax.set_xlabel("Onset difference (classical - topology, in epochs)")
    ax.set_title("Topology First = Positive")

    ax = axes[1]
    topo = np.asarray(results["topo_onsets"], dtype=float)
    classical = np.asarray(results["classical_onsets"].get("lempel_ziv", []), dtype=float)
    valid = ~(np.isnan(topo) | np.isnan(classical))
    if np.any(valid):
        ax.scatter(topo[valid], classical[valid], s=60, alpha=0.7)
        lim = max(np.max(topo[valid]), np.max(classical[valid])) * 1.1
        ax.plot([0, lim], [0, lim], "k--", alpha=0.4, label="simultaneous")
        ax.set_xlabel("Topological onset")
        ax.set_ylabel("Lempel-Ziv onset")
        ax.legend()
    ax.set_title("Per-Subject Primary Comparison")

    plt.tight_layout()
    out_path = FIGURES_DIR / "group_temporal_ordering.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved figure: {out_path.name}")


# ========== MAIN ==========

def main():
    combined_path = RESULTS_DIR / "all_subjects_metrics.csv"
    if not combined_path.exists():
        print("No metrics file found. Run 03_compute_metrics.py first.")
        return

    df = pd.read_csv(combined_path)
    if df.empty:
        print("The metrics file is empty.")
        return

    print(f"Loaded {len(df)} epochs from {df['subject'].nunique()} subjects.\n")
    print("Running acquisition-ordered temporal ordering analysis...")
    results, onset_df = analyze_temporal_ordering(df)
    print(f"  Valid subjects: {len(results['subjects'])}\n")

    if len(results["subjects"]) < 3:
        print("Too few subjects with detected onsets for group statistics.")
        print("This usually means the baseline/rest ordering has not been preserved yet.")
        return

    onset_path = RESULTS_DIR / "subject_onsets.csv"
    onset_df.to_csv(onset_path, index=False)

    print("Computing statistics...")
    stats_df = run_statistics(results)
    stats_path = RESULTS_DIR / "temporal_ordering_stats.csv"
    stats_df.to_csv(stats_path, index=False)

    print(f"\n{'=' * 60}")
    print("RESULTS: Acquisition-Ordered Temporal Ordering Test")
    print(f"{'=' * 60}")
    print(stats_df.to_string(index=False))
    print(f"\nSaved onset table: {onset_path}")
    print(f"Saved stats table: {stats_path}")

    n_supported = int(stats_df["nft_supported"].sum()) if not stats_df.empty else 0
    n_total = int(len(stats_df))
    print(
        "\nNFT proxy prediction supported (CI entirely > 0): "
        f"{n_supported}/{n_total} classical metrics"
    )

    print("\nGenerating figures...")
    for subject in results["subjects"][:3]:
        plot_temporal_ordering(df, results, subject)
    plot_group_results(stats_df, results)

    print("\nDone. Check figures/ and results/ directories.")


if __name__ == "__main__":
    main()
