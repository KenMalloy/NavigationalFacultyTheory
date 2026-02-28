"""
Step 3: Compute classical and topological metrics per epoch.

This stage preserves recording-level metadata so the temporal analysis can order
epochs by actual acquisition time rather than by guessed state labels.
"""
from __future__ import annotations

from pathlib import Path

from joblib import Parallel, delayed
import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import butter, hilbert, sosfilt
from gtda.homology import VietorisRipsPersistence

from config import (
    PROCESSED_DIR,
    RESULTS_DIR,
    SFREQ_TARGET,
    FREQ_BANDS,
    HOMOLOGY_DIMENSIONS,
    FILTRATION_MAX,
    FILTRATION_STEPS,
    WORKSPACE_DIR,
)


# ========== CLASSICAL METRICS ==========

def band_power(epoch: np.ndarray, sfreq: float) -> dict:
    """Relative and absolute power per band, averaged across channels."""
    nperseg = min(epoch.shape[-1], int(sfreq * 2))
    freqs, psd = signal.welch(epoch, fs=sfreq, nperseg=nperseg, axis=-1)
    total_power_channels = np.trapz(psd, freqs, axis=-1)
    total_power = float(np.mean(total_power_channels))

    result: dict[str, float] = {}
    for band_name, (fmin, fmax) in FREQ_BANDS.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(mask):
            band_abs = 0.0
        else:
            band_abs = float(np.mean(np.trapz(psd[:, mask], freqs[mask], axis=-1)))
        result[f"power_{band_name}_abs"] = band_abs
        result[f"power_{band_name}_rel"] = band_abs / total_power if total_power > 0 else 0.0

    result["power_total"] = total_power
    return result


def spectral_edge_frequency(epoch: np.ndarray, sfreq: float, pct: float = 0.95) -> float:
    """Frequency below which pct of total power lies."""
    nperseg = min(epoch.shape[-1], int(sfreq * 2))
    freqs, psd = signal.welch(epoch, fs=sfreq, nperseg=nperseg, axis=-1)
    psd_mean = np.mean(psd, axis=0)
    total = np.sum(psd_mean)
    if total <= 0:
        return 0.0
    cumulative = np.cumsum(psd_mean) / total
    idx = int(np.searchsorted(cumulative, pct))
    return float(freqs[min(idx, len(freqs) - 1)])


def rms_amplitude(epoch: np.ndarray) -> float:
    """Root mean square amplitude across the full epoch."""
    return float(np.sqrt(np.mean(epoch ** 2)))


def lempel_ziv_complexity(epoch: np.ndarray) -> float:
    """
    Lempel-Ziv complexity of a median-binarized multichannel epoch.

    This is a simple LZ76-style proxy suitable for relative comparisons, not a
    full compression-theoretic treatment.
    """
    binary = (epoch > np.median(epoch, axis=1, keepdims=True)).astype(np.uint8)
    sequence = binary.ravel()
    n = int(sequence.size)
    if n == 0:
        return 0.0

    i = 0
    complexity = 1
    while i < n - 1:
        match_len = 1
        while i + match_len < n and np.array_equal(
            sequence[i : i + match_len],
            sequence[i + 1 : i + 1 + match_len],
        ):
            match_len += 1
        complexity += 1
        i += match_len

    return float(complexity * np.log2(n) / n)


def functional_connectivity(epoch: np.ndarray, sfreq: float, band: tuple[float, float]) -> float:
    """Mean weighted phase lag index across channel pairs."""
    fmin, fmax = band
    sos = butter(4, [fmin, fmax], btype="band", fs=sfreq, output="sos")
    filtered = sosfilt(sos, epoch, axis=1)
    analytic = hilbert(filtered, axis=1)

    n_channels = analytic.shape[0]
    values: list[float] = []
    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            imag_cross = np.imag(analytic[i] * np.conj(analytic[j]))
            denominator = np.mean(np.abs(imag_cross))
            if denominator <= 1e-10:
                values.append(0.0)
                continue
            values.append(float(np.abs(np.mean(imag_cross)) / denominator))
    return float(np.mean(values)) if values else 0.0


def compute_classical(epoch: np.ndarray, sfreq: float) -> dict:
    result: dict[str, float] = {}
    result.update(band_power(epoch, sfreq))
    result["sef95"] = spectral_edge_frequency(epoch, sfreq)
    result["rms"] = rms_amplitude(epoch)
    result["lempel_ziv"] = lempel_ziv_complexity(epoch)
    result["wpli_alpha"] = functional_connectivity(epoch, sfreq, (8.0, 13.0))
    result["wpli_gamma"] = functional_connectivity(epoch, sfreq, (30.0, 45.0))
    return result


# ========== TOPOLOGICAL METRICS ==========

def correlation_distance_matrix(epoch: np.ndarray) -> np.ndarray:
    """
    Compute a channel correlation distance matrix.

    distance_ij = 1 - |corr(ch_i, ch_j)|
    """
    corr = np.corrcoef(epoch)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 1.0)
    dist = 1.0 - np.abs(corr)
    np.fill_diagonal(dist, 0.0)
    dist = (dist + dist.T) / 2.0
    return np.clip(dist, 0.0, FILTRATION_MAX)


def compute_persistent_homology(distance_matrix: np.ndarray) -> np.ndarray:
    """Run Vietoris-Rips persistence on a single distance matrix."""
    vr = VietorisRipsPersistence(
        metric="precomputed",
        homology_dimensions=HOMOLOGY_DIMENSIONS,
        max_edge_length=FILTRATION_MAX,
        n_jobs=1,
    )
    return vr.fit_transform(distance_matrix[np.newaxis, :, :])


def _betti_curve(points: np.ndarray) -> np.ndarray:
    grid = np.linspace(0.0, FILTRATION_MAX, FILTRATION_STEPS)
    if points.size == 0:
        return np.zeros_like(grid)
    births = points[:, 0][:, np.newaxis]
    deaths = points[:, 1][:, np.newaxis]
    alive = (births <= grid) & (grid < deaths)
    return alive.sum(axis=0).astype(float)


def extract_topological_features(diagrams: np.ndarray) -> dict:
    """Summarize persistence diagrams into scalar features."""
    result: dict[str, float] = {}
    diagram = diagrams[0]
    topo_complexity = 0.0

    for dim in HOMOLOGY_DIMENSIONS:
        points = diagram[diagram[:, 2] == dim][:, :2]
        if points.size == 0:
            points = np.empty((0, 2))
        finite = np.isfinite(points).all(axis=1)
        points = points[finite]
        lifetimes = np.clip(points[:, 1] - points[:, 0], 0.0, None) if len(points) else np.array([])
        curve = _betti_curve(points)

        result[f"betti_{dim}_max"] = float(np.max(curve)) if curve.size else 0.0
        result[f"betti_{dim}_mean"] = float(np.mean(curve)) if curve.size else 0.0
        result[f"betti_{dim}_auc"] = float(np.trapz(curve, dx=FILTRATION_MAX / max(FILTRATION_STEPS - 1, 1)))
        result[f"n_features_{dim}"] = float(len(lifetimes))
        result[f"total_persistence_{dim}"] = float(np.sum(lifetimes))

        if len(lifetimes) and np.sum(lifetimes) > 0:
            probs = lifetimes / np.sum(lifetimes)
            entropy = float(-(probs * np.log(probs + 1e-12)).sum())
        else:
            entropy = 0.0
        result[f"persistence_entropy_{dim}"] = entropy

        if dim > 0:
            topo_complexity += entropy + result[f"total_persistence_{dim}"]

    result["topo_complexity"] = float(topo_complexity)
    return result


def compute_topological(epoch: np.ndarray) -> dict:
    dist = correlation_distance_matrix(epoch)
    diagrams = compute_persistent_homology(dist)
    return extract_topological_features(diagrams)


# ========== MAIN LOOP ==========

def process_epoch(epoch: np.ndarray, sfreq: float, idx: int) -> dict:
    row = {"epoch_idx": idx}
    row.update(compute_classical(epoch, sfreq))
    row.update(compute_topological(epoch))
    return row


def process_recording(recording: pd.Series) -> pd.DataFrame:
    """Compute all epoch-level metrics for one preprocessed recording."""
    epoch_file = Path(recording["epoch_file"])
    if not epoch_file.is_absolute():
        epoch_file = (WORKSPACE_DIR / epoch_file).resolve()
    data = np.load(epoch_file)
    sfreq = float(recording.get("sfreq", SFREQ_TARGET))
    bids_stem = recording.get("bids_stem", recording.get("stem"))

    print(
        f"  {bids_stem}: {data.shape[0]} epochs, "
        f"{data.shape[1]} ch, {data.shape[2]} samples"
    )

    rows = Parallel(n_jobs=-1, verbose=0)(
        delayed(process_epoch)(data[i], sfreq, i)
        for i in range(data.shape[0])
    )
    df = pd.DataFrame(rows)

    for key in (
        "subject",
        "task",
        "acquisition",
        "run",
        "acq_time",
        "source_file",
        "epoch_file",
    ):
        df[key] = recording[key]
    df["bids_stem"] = bids_stem

    return df


def main():
    manifest_path = PROCESSED_DIR / "recordings_manifest.csv"
    if not manifest_path.exists():
        print("No recordings manifest found. Run 02_preprocess.py first.")
        return

    manifest = pd.read_csv(manifest_path)
    if manifest.empty:
        print("The manifest is empty. Check preprocessing output.")
        return

    print(f"Found {len(manifest)} recordings in the manifest.\n")
    all_dfs: list[pd.DataFrame] = []

    for recording in manifest.sort_values(["subject", "acq_time", "task", "run"]).itertuples(index=False):
        row = pd.Series(recording._asdict())
        bids_stem = row.get("bids_stem", row.get("stem"))
        print(f"\nProcessing {row['subject']} / {bids_stem}...")
        df = process_recording(row)
        all_dfs.append(df)

        out_path = RESULTS_DIR / f"{bids_stem}_metrics.csv"
        df.to_csv(out_path, index=False)
        print(f"  Saved {out_path}")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined_path = RESULTS_DIR / "all_subjects_metrics.csv"
    combined.to_csv(combined_path, index=False)

    metric_columns = [
        c
        for c in combined.columns
        if c
        not in {
            "subject",
            "task",
            "acquisition",
            "run",
            "bids_stem",
            "acq_time",
            "source_file",
            "epoch_file",
            "epoch_idx",
        }
    ]
    summary = (
        combined.groupby(["subject", "task", "acquisition", "run", "bids_stem", "acq_time"], dropna=False)[metric_columns]
        .median()
        .reset_index()
        .sort_values(["subject", "acq_time", "task", "run"], na_position="last")
    )
    summary_path = RESULTS_DIR / "recording_summary_metrics.csv"
    summary.to_csv(summary_path, index=False)

    print(f"\nCombined epoch-level results: {combined_path}")
    print(f"Recording-level summary: {summary_path}")
    print(f"Total epochs: {len(combined)}")
    print("Next: run 04_temporal_ordering.py")


if __name__ == "__main__":
    main()
