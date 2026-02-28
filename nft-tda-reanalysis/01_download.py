"""
Step 1: Download OpenNeuro dataset DS005620.
Propofol sedation, 21 subjects, EEG, BIDS format, CC0.

Run once. ~2-5 GB depending on dataset size.
"""
import openneuro
from config import DATASET_ID, RAW_DIR

print(f"Downloading {DATASET_ID} to {RAW_DIR}...")
print("This may take a while on first run.\n")

openneuro.download(
    dataset=DATASET_ID,
    target_dir=str(RAW_DIR / DATASET_ID),
    include="*.eeg,*.vhdr,*.vmrk,*.json,*.tsv,*.set,*.fdt,*edf*",
    # Skip non-EEG files (MRI, etc.) if present
)

print(f"\nDone. Data saved to {RAW_DIR / DATASET_ID}")
print("Next: run 02_preprocess.py")
