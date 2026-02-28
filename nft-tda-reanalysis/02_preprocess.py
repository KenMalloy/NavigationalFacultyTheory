"""
Step 2: Preprocess DS005620 EEG into fixed-length epochs.

For this dataset, the usable state labels come from the BIDS filenames and the
`sub-*/sub-*_scans.tsv` acquisition timestamps, not from induction markers
inside the rest recordings. The preprocessing stage therefore preserves the
recording-level metadata needed to order awake/sed/sed2 runs later on.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

import mne
import numpy as np
import pandas as pd

from config import (
    RAW_DIR,
    PROCESSED_DIR,
    DATASET_ID,
    SFREQ_TARGET,
    HIGHPASS,
    LOWPASS,
    EPOCH_DURATION,
    EPOCH_OVERLAP,
    ICA_N_COMPONENTS,
    PRIMARY_RECORDINGS,
    EXCLUDED_ACQUISITIONS,
)


mne.set_log_level("WARNING")

SUPPORTED_SUFFIXES = (".vhdr", ".set", ".edf", ".bdf")
BIDS_EEG_RE = re.compile(
    r"(?P<subject>sub-[^_]+)_task-(?P<task>[^_]+)_acq-(?P<acquisition>[^_]+)"
    r"(?:_run-(?P<run>\d+))?_eeg(?P<suffix>\.[^.]+)$"
)


@dataclass(frozen=True)
class RecordingSpec:
    subject: str
    task: str
    acquisition: str
    run: int | None
    stem: str
    path: Path


def parse_recording_spec(filepath: Path) -> RecordingSpec | None:
    """Parse DS005620 BIDS EEG filenames into structured metadata."""
    match = BIDS_EEG_RE.match(filepath.name)
    if not match:
        return None

    data = match.groupdict()
    suffix = data["suffix"].lower()
    if suffix not in SUPPORTED_SUFFIXES:
        return None

    return RecordingSpec(
        subject=data["subject"],
        task=data["task"],
        acquisition=data["acquisition"],
        run=int(data["run"]) if data["run"] is not None else None,
        stem=filepath.name[: -len(suffix)],
        path=filepath,
    )


def is_primary_recording(spec: RecordingSpec) -> bool:
    return (spec.task, spec.acquisition) in PRIMARY_RECORDINGS


def find_recordings(data_dir: Path) -> list[RecordingSpec]:
    """Find and filter recordings relevant to the first-pass proxy experiment."""
    files: list[Path] = []
    for pattern in ("*.vhdr", "*.set", "*.edf", "*.bdf"):
        files.extend(data_dir.rglob(pattern))

    recordings: list[RecordingSpec] = []
    for filepath in sorted(files):
        spec = parse_recording_spec(filepath)
        if spec is None:
            continue
        if spec.acquisition in EXCLUDED_ACQUISITIONS:
            continue
        if not is_primary_recording(spec):
            continue
        recordings.append(spec)
    return recordings


def load_scan_times(data_dir: Path) -> dict[tuple[str, str], str]:
    """Map (subject, bids_stem) -> acquisition timestamp from scans.tsv."""
    mapping: dict[tuple[str, str], str] = {}
    for scans_file in sorted(data_dir.glob("sub-*/sub-*_scans.tsv")):
        subject = scans_file.parent.name
        scans = pd.read_csv(scans_file, sep="\t", encoding="utf-8-sig")
        for row in scans.itertuples(index=False):
            filename = Path(getattr(row, "filename"))
            stem = filename.name.replace(".vhdr", "")
            mapping[(subject, stem)] = getattr(row, "acq_time", "")
    return mapping


def read_raw(filepath: Path) -> mne.io.BaseRaw:
    suffix = filepath.suffix.lower()
    if suffix == ".vhdr":
        return mne.io.read_raw_brainvision(filepath, preload=True)
    if suffix == ".set":
        return mne.io.read_raw_eeglab(filepath, preload=True)
    if suffix in (".edf", ".bdf"):
        return mne.io.read_raw_edf(filepath, preload=True)
    raise ValueError(f"Unsupported EEG format: {filepath.suffix}")


def preprocess_raw(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """Apply a lightweight, reproducible preprocessing stack."""
    raw.filter(l_freq=HIGHPASS, h_freq=LOWPASS, fir_design="firwin")

    if raw.info["sfreq"] != SFREQ_TARGET:
        raw.resample(SFREQ_TARGET)

    raw.set_eeg_reference("average", projection=False)

    # ICA is useful here, but keep it soft-fail so a single recording does not
    # halt the full manifest build.
    if raw.info["nchan"] > 2:
        try:
            ica = mne.preprocessing.ICA(
                n_components=min(ICA_N_COMPONENTS, raw.info["nchan"] - 1),
                random_state=42,
                max_iter="auto",
            )
            ica.fit(raw)
            eog_chs = mne.pick_types(raw.info, eog=True)
            if len(eog_chs) > 0:
                eog_indices, _ = ica.find_bads_eog(raw)
                ica.exclude = eog_indices[:2]
            ica.apply(raw)
        except Exception as exc:
            print(f"    ICA skipped: {exc}")

    return raw


def make_epochs(raw: mne.io.BaseRaw) -> np.ndarray:
    """Segment one recording into overlapping fixed-length epochs."""
    epochs = mne.make_fixed_length_epochs(
        raw,
        duration=EPOCH_DURATION,
        overlap=EPOCH_OVERLAP,
        preload=True,
        reject_by_annotation=True,
    )
    return epochs.get_data(copy=True)


def preprocess_recording(spec: RecordingSpec) -> tuple[np.ndarray, dict]:
    """Preprocess one recording and return epochs plus lightweight metadata."""
    raw = read_raw(spec.path)
    raw = preprocess_raw(raw)
    data = make_epochs(raw).astype(np.float32, copy=False)

    metadata = {
        "n_epochs": int(data.shape[0]),
        "n_channels": int(data.shape[1]),
        "n_samples": int(data.shape[2]),
        "sfreq": float(raw.info["sfreq"]),
        "channel_names": ",".join(raw.ch_names),
    }
    return data, metadata


def main():
    data_dir = RAW_DIR / DATASET_ID
    recordings = find_recordings(data_dir)

    if not recordings:
        print(f"No primary-analysis EEG files found in {data_dir}")
        print("Did you run 01_download.py first?")
        return

    scan_times = load_scan_times(data_dir)
    manifest_rows: list[dict] = []

    print(f"Found {len(recordings)} recordings for the proxy experiment.\n")

    for index, spec in enumerate(recordings, start=1):
        print(
            f"[{index}/{len(recordings)}] {spec.subject} "
            f"{spec.task}/{spec.acquisition} "
            f"{f'run-{spec.run}' if spec.run is not None else 'run-na'}"
        )

        try:
            data, metadata = preprocess_recording(spec)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            continue

        subject_dir = PROCESSED_DIR / spec.subject
        subject_dir.mkdir(parents=True, exist_ok=True)

        epoch_path = subject_dir / f"{spec.stem}_epochs.npy"
        np.save(epoch_path, data)

        manifest_row = {
            **asdict(spec),
            "bids_stem": spec.stem,
            **metadata,
            "source_file": str(spec.path),
            "epoch_file": str(epoch_path),
            "acq_time": scan_times.get((spec.subject, spec.stem), ""),
            "included_in_primary_analysis": True,
        }
        manifest_rows.append(manifest_row)

        print(
            f"  Saved {epoch_path.name} | "
            f"{metadata['n_epochs']} epochs, {metadata['n_channels']} ch"
        )

    if not manifest_rows:
        print("No recordings were processed successfully.")
        return

    manifest = (
        pd.DataFrame(manifest_rows)
        .sort_values(["subject", "acq_time", "task", "run"], na_position="last")
        .reset_index(drop=True)
    )
    manifest_path = PROCESSED_DIR / "recordings_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    print(f"\nSaved manifest: {manifest_path}")
    print(f"Processed recordings: {len(manifest)}")
    print("Next: run 03_compute_metrics.py")


if __name__ == "__main__":
    main()
