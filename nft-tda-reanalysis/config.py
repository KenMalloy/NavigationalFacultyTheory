"""
Configuration for NFT topological reanalysis.
Prediction XIII.B / XIII.H: topological complexity tracks consciousness level
and declines BEFORE classical metrics during sedation-related transitions.
"""
from pathlib import Path

# --- Project paths ---
# Keep all downloaded data and derived outputs at the workspace level so the
# pipeline can be resumed consistently across scripts and ad hoc runs.
PROJECT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = WORKSPACE_DIR / "results"
FIGURES_DIR = WORKSPACE_DIR / "figures"

for d in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- Dataset ---
# OpenNeuro DS005620: propofol sedation, 21 subjects, BIDS format
DATASET_ID = "ds005620"
DATASET_TAG = "1.0.0"

# Primary analysis subset for the first-pass proxy experiment:
# awake eyes-closed baseline + ordered rest recordings during sedation.
PRIMARY_RECORDINGS = (
    ("awake", "EC"),
    ("sed", "rest"),
    ("sed2", "rest"),
)
EXCLUDED_ACQUISITIONS = {"tms"}
AWAKE_BASELINE_ACQ = "EC"
POST_BASELINE_TASKS = ("sed", "sed2")

# --- EEG preprocessing ---
SFREQ_TARGET = 250          # downsample to 250 Hz
HIGHPASS = 0.5               # Hz
LOWPASS = 45.0               # Hz
EPOCH_DURATION = 4.0         # seconds per sliding window
EPOCH_OVERLAP = 2.0          # seconds overlap (50%)
BAD_CHANNEL_THRESHOLD = 0.3  # correlation threshold for bad channel detection
ICA_N_COMPONENTS = 20        # ICA components for artifact rejection

# --- Recording selection ---
# DS005620 uses BIDS task/acq labels rather than induction markers inside the
# rest recordings, so the analysis should preserve these labels directly.

# --- Classical metrics ---
FREQ_BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}

# --- Topological metrics ---
# Persistent homology dimensions to compute
HOMOLOGY_DIMENSIONS = [0, 1, 2]  # β_0 through β_2
# H_3 is expensive and unstable for a first pass with channel-level scalp EEG.

# Filtration: Vietoris-Rips on channel correlation distance
# distance = 1 - |correlation|
FILTRATION_MAX = 1.5
FILTRATION_STEPS = 64

# --- Temporal ordering analysis ---
# Sliding window for transition analysis
TRANSITION_WINDOW = 2.0      # seconds
TRANSITION_STEP = 0.5        # seconds
# Number of bootstrap samples for onset detection
N_BOOTSTRAP = 1000
ONSET_THRESHOLD_PERCENTILE = 95  # from baseline distribution
ONSET_MIN_CONSECUTIVE = 3
