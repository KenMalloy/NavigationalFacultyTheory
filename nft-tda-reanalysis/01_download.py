"""
Step 1: Download OpenNeuro dataset DS005620.
Propofol sedation, 21 subjects, EEG, BIDS format, CC0.

This first-pass proxy experiment only needs:
  - awake eyes-closed baseline recordings
  - sed/sed2 rest recordings
  - scans/participants metadata to order runs later on
"""
import openneuro
from config import DATASET_ID, DATASET_TAG, RAW_DIR

print(f"Downloading {DATASET_ID} to {RAW_DIR}...")
print("This may take a while on first run.\n")

openneuro.download(
    dataset=DATASET_ID,
    tag=DATASET_TAG,
    target_dir=str(RAW_DIR / DATASET_ID),
    include=[
        "participants.tsv",
        "participants.json",
        "sub-*/sub-*_scans.tsv",
        "sub-*/eeg/*_task-awake_acq-EC_*",
        "sub-*/eeg/*_task-sed_acq-rest_*",
        "sub-*/eeg/*_task-sed2_acq-rest_*",
    ],
    max_concurrent_downloads=8,
)

print(f"\nDone. Data saved to {RAW_DIR / DATASET_ID}")
print("Next: run 02_preprocess.py")
