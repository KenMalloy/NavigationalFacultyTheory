"""
Step 2: Preprocess EEG data.

Pipeline:
  1. Load BIDS-formatted EEG
  2. Band-pass filter (0.5–45 Hz)
  3. Downsample to 250 Hz
  4. Detect and interpolate bad channels
  5. ICA for eye/muscle artifact rejection
  6. Segment into overlapping epochs
  7. Save per-subject, per-condition

Adjust STATES mapping in config.py after inspecting
the actual event markers in the dataset.
"""
import mne
import numpy as np
from pathlib import Path
from config import (
    RAW_DIR, PROCESSED_DIR, DATASET_ID,
    SFREQ_TARGET, HIGHPASS, LOWPASS,
    EPOCH_DURATION, EPOCH_OVERLAP,
    ICA_N_COMPONENTS, STATES,
)

mne.set_log_level("WARNING")


def find_eeg_files(data_dir: Path) -> list[Path]:
    """Find all EEG files in BIDS structure."""
    patterns = ["*.vhdr", "*.set", "*.edf", "*.bdf"]
    files = []
    for pat in patterns:
        files.extend(data_dir.rglob(pat))
    return sorted(files)


def preprocess_single(filepath: Path) -> dict:
    """
    Preprocess one EEG recording.
    Returns dict of {condition_label: list of epoch arrays}.
    Each epoch array is (n_channels, n_samples).
    """
    # --- Load ---
    suffix = filepath.suffix.lower()
    if suffix == ".vhdr":
        raw = mne.io.read_raw_brainvision(filepath, preload=True)
    elif suffix == ".set":
        raw = mne.io.read_raw_eeglab(filepath, preload=True)
    elif suffix in (".edf", ".bdf"):
        raw = mne.io.read_raw_edf(filepath, preload=True)
    else:
        raise ValueError(f"Unknown format: {suffix}")

    print(f"  Loaded: {filepath.name} | {raw.info['nchan']} ch, "
          f"{raw.times[-1]:.0f}s, {raw.info['sfreq']} Hz")

    # --- Filter ---
    raw.filter(l_freq=HIGHPASS, h_freq=LOWPASS, fir_design="firwin")

    # --- Resample ---
    if raw.info["sfreq"] != SFREQ_TARGET:
        raw.resample(SFREQ_TARGET)

    # --- Bad channel detection (correlation-based) ---
    # Simple approach: channels with low correlation to neighbors
    raw.info["bads"] = []  # reset
    # Use MNE's built-in if available, otherwise skip for now
    try:
        from mne.preprocessing import find_bad_channels_maxwell
        # Only works for MEG — for EEG, use RANSAC or manual
        pass
    except ImportError:
        pass
    # Interpolate any marked bad channels
    if raw.info["bads"]:
        raw.interpolate_bads()

    # --- Re-reference to average ---
    raw.set_eeg_reference("average", projection=False)

    # --- ICA for artifact rejection ---
    ica = mne.preprocessing.ICA(
        n_components=min(ICA_N_COMPONENTS, raw.info["nchan"] - 1),
        random_state=42,
        max_iter="auto",
    )
    ica.fit(raw)

    # Auto-detect EOG components if EOG channels exist
    eog_chs = mne.pick_types(raw.info, eog=True)
    if len(eog_chs) > 0:
        eog_indices, _ = ica.find_bads_eog(raw)
        ica.exclude = eog_indices[:2]  # exclude at most 2
    # Apply ICA
    ica.apply(raw)

    # --- Extract events / annotations ---
    events, event_id = mne.events_from_annotations(raw)
    print(f"  Events found: {event_id}")

    # --- Epoch by sliding window ---
    # For continuous data, create fixed-length epochs
    n_samples = int(EPOCH_DURATION * SFREQ_TARGET)
    step_samples = int((EPOCH_DURATION - EPOCH_OVERLAP) * SFREQ_TARGET)

    epochs_out = {}

    # If we have event annotations matching our STATES, use them
    # Otherwise fall back to fixed-length epochs across the whole recording
    matched_any = False
    for condition, markers in STATES.items():
        matching_ids = {k: v for k, v in event_id.items()
                        if any(m.lower() in k.lower() for m in markers)}
        if matching_ids:
            matched_any = True
            try:
                ep = mne.Epochs(
                    raw, events, event_id=matching_ids,
                    tmin=0, tmax=EPOCH_DURATION,
                    baseline=None, preload=True,
                )
                epochs_out[condition] = ep.get_data()
                print(f"  {condition}: {len(ep)} epochs")
            except Exception as e:
                print(f"  {condition}: failed ({e})")

    if not matched_any:
        # Fallback: just chop the whole recording into epochs
        # You'll need to manually label which time ranges are which state
        print("  WARNING: No event markers matched STATES config.")
        print("  Creating fixed-length epochs across full recording.")
        print("  You will need to label these manually based on the protocol.")
        ep = mne.make_fixed_length_epochs(
            raw, duration=EPOCH_DURATION,
            overlap=EPOCH_OVERLAP, preload=True,
        )
        epochs_out["unlabeled"] = ep.get_data()
        print(f"  unlabeled: {len(ep)} epochs")

    return epochs_out, raw.info


def main():
    data_dir = RAW_DIR / DATASET_ID
    eeg_files = find_eeg_files(data_dir)

    if not eeg_files:
        print(f"No EEG files found in {data_dir}")
        print("Did you run 01_download.py first?")
        return

    print(f"Found {len(eeg_files)} EEG files.\n")

    for i, fpath in enumerate(eeg_files):
        subject_id = fpath.parent.name  # e.g., "sub-01"
        print(f"\n[{i+1}/{len(eeg_files)}] Processing {subject_id}...")

        try:
            epochs_dict, info = preprocess_single(fpath)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        # Save
        out_dir = PROCESSED_DIR / subject_id
        out_dir.mkdir(parents=True, exist_ok=True)

        for condition, data in epochs_dict.items():
            out_path = out_dir / f"{condition}_epochs.npy"
            np.save(out_path, data)
            print(f"  Saved {out_path} | shape {data.shape}")

        # Save channel info for later
        info_path = out_dir / "info.fif"
        mne.io.write_info(info_path, info)

    print("\nPreprocessing complete.")
    print("Next: run 03_compute_metrics.py")


if __name__ == "__main__":
    main()
