"""
Step 3: Compute classical and topological metrics per epoch.

CLASSICAL METRICS (what existing analyses already do):
  - Band power (delta, theta, alpha, beta, gamma)
  - Spectral edge frequency (SEF95)
  - Signal amplitude (RMS)
  - Lempel-Ziv complexity
  - Functional connectivity (wPLI in alpha/gamma bands)

TOPOLOGICAL METRICS (the NFT-specific analysis):
  - Persistent homology of channel correlation matrices
  - Betti numbers β_0 through β_3 (or higher if feasible)
  - Persistence entropy
  - Total persistence (sum of lifetimes)
  - Persistence landscapes (for statistical testing)

The key prediction: topological metrics should diverge from classical
metrics during TRANSITIONS — topology drops first on induction,
recovers last on emergence.
"""
import numpy as np
from scipy import signal
from scipy.spatial.distance import squareform
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import (
    PersistenceEntropy,
    Amplitude,
    NumberOfPoints,
    BettiCurve,
)
from joblib import Parallel, delayed
from pathlib import Path
import pandas as pd

from config import (
    PROCESSED_DIR, RESULTS_DIR,
    SFREQ_TARGET, FREQ_BANDS,
    HOMOLOGY_DIMENSIONS, FILTRATION_MAX, FILTRATION_STEPS,
)


# ========== CLASSICAL METRICS ==========

def band_power(epoch: np.ndarray, sfreq: float) -> dict:
    """Relative power in each frequency band, averaged across channels."""
    freqs, psd = signal.welch(epoch, fs=sfreq, nperseg=sfreq * 2)
    total_power = np.trapz(psd, freqs, axis=-1).mean()

    result = {}
    for band_name, (fmin, fmax) in FREQ_BANDS.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        bp = np.trapz(psd[:, mask], freqs[mask], axis=-1).mean()
        result[f"power_{band_name}_rel"] = bp / total_power
        result[f"power_{band_name}_abs"] = bp
    result["power_total"] = total_power
    return result


def spectral_edge_frequency(epoch: np.ndarray, sfreq: float,
                             pct: float = 0.95) -> float:
    """Frequency below which pct% of total power lies."""
    freqs, psd = signal.welch(epoch, fs=sfreq, nperseg=sfreq * 2)
    psd_mean = psd.mean(axis=0)
    cumpower = np.cumsum(psd_mean)
    cumpower /= cumpower[-1]
    idx = np.searchsorted(cumpower, pct)
    return freqs[min(idx, len(freqs) - 1)]


def rms_amplitude(epoch: np.ndarray) -> float:
    """Root mean square amplitude, averaged across channels."""
    return np.sqrt(np.mean(epoch ** 2))


def lempel_ziv_complexity(epoch: np.ndarray) -> float:
    """
    Lempel-Ziv complexity of binarized multichannel signal.
    Binarize by median split per channel, concatenate, compute LZ76.
    """
    # Binarize each channel by its median
    binary = (epoch > np.median(epoch, axis=1, keepdims=True)).astype(int)
    # Concatenate channels into single binary string
    s = binary.flatten()

    # LZ76 complexity
    n = len(s)
    if n == 0:
        return 0.0
    i, k, l = 0, 1, 1
    c = 1
    while k < n:
        if s[k] != s[k - l]:
            i += 1
            if i == k:
                c += 1
                k += 1
                i = 0
                l = k
            else:
                l = k - i
        else:
            k += 1
    c += 1
    # Normalize
    return c * np.log2(n) / n if n > 0 else 0.0


def functional_connectivity(epoch: np.ndarray, sfreq: float,
                             band: tuple = (8, 13)) -> float:
    """
    Weighted Phase Lag Index in a given frequency band.
    Returns mean connectivity strength.
    """
    from scipy.signal import hilbert, butter, sosfilt

    fmin, fmax = band
    sos = butter(4, [fmin, fmax], btype="band", fs=sfreq, output="sos")
    filtered = sosfilt(sos, epoch, axis=1)
    analytic = hilbert(filtered, axis=1)
    phase = np.angle(analytic)

    n_ch = phase.shape[0]
    wpli_vals = []
    for i in range(n_ch):
        for j in range(i + 1, n_ch):
            dphi = phase[i] - phase[j]
            imag_cross = np.sin(dphi)
            wpli = np.abs(np.mean(imag_cross)) / np.mean(np.abs(imag_cross) + 1e-10)
            wpli_vals.append(wpli)
    return np.mean(wpli_vals)


def compute_classical(epoch: np.ndarray, sfreq: float) -> dict:
    """All classical metrics for one epoch."""
    result = {}
    result.update(band_power(epoch, sfreq))
    result["sef95"] = spectral_edge_frequency(epoch, sfreq)
    result["rms"] = rms_amplitude(epoch)
    result["lempel_ziv"] = lempel_ziv_complexity(epoch)
    result["wpli_alpha"] = functional_connectivity(epoch, sfreq, (8, 13))
    result["wpli_gamma"] = functional_connectivity(epoch, sfreq, (30, 45))
    return result


# ========== TOPOLOGICAL METRICS ==========

def correlation_distance_matrix(epoch: np.ndarray) -> np.ndarray:
    """
    Compute channel-by-channel correlation distance matrix.
    distance_ij = 1 - |corr(ch_i, ch_j)|
    Returns (n_channels, n_channels) distance matrix.
    """
    corr = np.corrcoef(epoch)  # (n_ch, n_ch)
    np.fill_diagonal(corr, 1.0)
    dist = 1.0 - np.abs(corr)
    np.fill_diagonal(dist, 0.0)
    # Ensure symmetry and non-negativity
    dist = (dist + dist.T) / 2
    dist = np.maximum(dist, 0.0)
    return dist


def compute_persistent_homology(distance_matrix: np.ndarray) -> np.ndarray:
    """
    Compute persistent homology from a distance matrix.
    Returns persistence diagrams as array of (birth, death, dimension).
    """
    # giotto-tda expects (n_samples, n_points, n_points) for precomputed
    dm = distance_matrix[np.newaxis, :, :]  # add batch dim

    vr = VietorisRipsPersistence(
        metric="precomputed",
        homology_dimensions=HOMOLOGY_DIMENSIONS,
        max_edge_length=FILTRATION_MAX,
        n_jobs=1,
    )
    diagrams = vr.fit_transform(dm)
    return diagrams  # shape (1, n_features, 3)


def extract_topological_features(diagrams: np.ndarray) -> dict:
    """
    Extract summary statistics from persistence diagrams.
    """
    result = {}

    # --- Betti numbers at multiple filtration thresholds ---
    betti_curve = BettiCurve(n_bins=FILTRATION_STEPS)
    curves = betti_curve.fit_transform(diagrams)  # (1, n_dims * n_bins)

    # Store max Betti number per dimension
    n_bins = FILTRATION_STEPS
    for i, dim in enumerate(HOMOLOGY_DIMENSIONS):
        curve_dim = curves[0, i * n_bins:(i + 1) * n_bins]
        result[f"betti_{dim}_max"] = float(np.max(curve_dim))
        result[f"betti_{dim}_mean"] = float(np.mean(curve_dim))
        result[f"betti_{dim}_auc"] = float(np.sum(curve_dim))

    # --- Persistence entropy (topological complexity summary) ---
    pe = PersistenceEntropy()
    entropies = pe.fit_transform(diagrams)
    for i, dim in enumerate(HOMOLOGY_DIMENSIONS):
        result[f"persistence_entropy_{dim}"] = float(entropies[0, i])

    # --- Total persistence (sum of bar lifetimes) ---
    amp = Amplitude(metric="persistence")
    amplitudes = amp.fit_transform(diagrams)
    for i, dim in enumerate(HOMOLOGY_DIMENSIONS):
        result[f"total_persistence_{dim}"] = float(amplitudes[0, i])

    # --- Number of topological features per dimension ---
    nop = NumberOfPoints()
    counts = nop.fit_transform(diagrams)
    for i, dim in enumerate(HOMOLOGY_DIMENSIONS):
        result[f"n_features_{dim}"] = float(counts[0, i])

    # --- Composite topological complexity score ---
    # Sum of persistence entropies across dimensions (single scalar)
    result["topo_complexity"] = sum(
        result[f"persistence_entropy_{d}"] for d in HOMOLOGY_DIMENSIONS
    )

    return result


def compute_topological(epoch: np.ndarray) -> dict:
    """All topological metrics for one epoch."""
    dist = correlation_distance_matrix(epoch)
    diagrams = compute_persistent_homology(dist)
    return extract_topological_features(diagrams)


# ========== MAIN LOOP ==========

def process_epoch(epoch: np.ndarray, sfreq: float, idx: int) -> dict:
    """Compute all metrics for a single epoch."""
    row = {"epoch_idx": idx}
    row.update(compute_classical(epoch, sfreq))
    row.update(compute_topological(epoch))
    return row


def process_subject(subject_dir: Path) -> pd.DataFrame:
    """Process all epochs for one subject."""
    all_rows = []
    sfreq = SFREQ_TARGET

    for npy_file in sorted(subject_dir.glob("*_epochs.npy")):
        condition = npy_file.stem.replace("_epochs", "")
        data = np.load(npy_file)  # (n_epochs, n_channels, n_samples)
        print(f"  {condition}: {data.shape[0]} epochs, "
              f"{data.shape[1]} ch, {data.shape[2]} samples")

        rows = Parallel(n_jobs=-1, verbose=0)(
            delayed(process_epoch)(data[i], sfreq, i)
            for i in range(data.shape[0])
        )

        for row in rows:
            row["condition"] = condition
        all_rows.extend(rows)

    return pd.DataFrame(all_rows)


def main():
    subject_dirs = sorted(PROCESSED_DIR.glob("sub-*"))

    if not subject_dirs:
        print("No processed data found. Run 02_preprocess.py first.")
        return

    print(f"Found {len(subject_dirs)} subjects.\n")
    all_dfs = []

    for sdir in subject_dirs:
        subject_id = sdir.name
        print(f"\nProcessing {subject_id}...")

        df = process_subject(sdir)
        df["subject"] = subject_id
        all_dfs.append(df)

        # Save per-subject
        out_path = RESULTS_DIR / f"{subject_id}_metrics.csv"
        df.to_csv(out_path, index=False)
        print(f"  Saved {out_path}")

    # Combine all subjects
    combined = pd.concat(all_dfs, ignore_index=True)
    combined_path = RESULTS_DIR / "all_subjects_metrics.csv"
    combined.to_csv(combined_path, index=False)
    print(f"\nCombined results: {combined_path}")
    print(f"Total epochs: {len(combined)}")
    print(f"Columns: {list(combined.columns)}")
    print("\nNext: run 04_temporal_ordering.py")


if __name__ == "__main__":
    main()
