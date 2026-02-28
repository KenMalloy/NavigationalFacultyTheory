"""
Configuration for NFT topological reanalysis.
Prediction XIII.B / XIII.H: topological complexity tracks consciousness level
and declines BEFORE classical metrics during transitions.
"""
from pathlib import Path

# --- Paths ---
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")

for d in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- Dataset ---
# OpenNeuro DS005620: propofol sedation, 21 subjects, BIDS format
DATASET_ID = "ds005620"

# --- EEG preprocessing ---
SFREQ_TARGET = 250          # downsample to 250 Hz
HIGHPASS = 0.5               # Hz
LOWPASS = 45.0               # Hz
EPOCH_DURATION = 4.0         # seconds per sliding window
EPOCH_OVERLAP = 2.0          # seconds overlap (50%)
BAD_CHANNEL_THRESHOLD = 0.3  # correlation threshold for bad channel detection
ICA_N_COMPONENTS = 20        # ICA components for artifact rejection

# --- Consciousness states (dataset-specific, adjust after inspecting events) ---
# These are placeholders — update once you inspect the actual event markers
STATES = {
    "awake": ["baseline", "pre_sedation"],
    "transition": ["induction"],       # the money window
    "sedated": ["deep_sedation", "propofol"],
    "recovery": ["emergence", "post_sedation"],
}

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
HOMOLOGY_DIMENSIONS = [0, 1, 2, 3]  # β_0 through β_3
# Higher dimensions (4+) are computationally expensive for full EEG
# but we should push as high as feasible

# Filtration: Vietoris-Rips on channel correlation distance
# distance = 1 - |correlation|
FILTRATION_MAX = 1.5
FILTRATION_STEPS = 100

# --- Temporal ordering analysis ---
# Sliding window for transition analysis
TRANSITION_WINDOW = 2.0      # seconds
TRANSITION_STEP = 0.5        # seconds
# Number of bootstrap samples for onset detection
N_BOOTSTRAP = 1000
ONSET_THRESHOLD_PERCENTILE = 95  # from baseline distribution
