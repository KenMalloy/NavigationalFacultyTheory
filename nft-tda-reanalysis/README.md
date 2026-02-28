# NFT Topological Reanalysis

Testing NFT Prediction XIII.B/XIII.H: **topological complexity tracks consciousness
level and declines before classical neural activity metrics during anesthetic
induction.**

## The prediction

Navigational Faculty Theory predicts that microtubule disruption (or, by proxy,
anesthetic-induced loss of consciousness) should reduce higher-dimensional
topological complexity of neural dynamics *before* reducing classical activity
metrics like spectral power, signal amplitude, or Lempel-Ziv complexity.

Classical models predict either the reverse order (topology follows activity)
or simultaneous reduction. This temporal ordering is a discriminative prediction
— no competing consciousness theory makes it.

## Pipeline

```
run_pipeline.py      → Convenience runner for the steps below
01_download.py       → Fetch OpenNeuro DS005620 (propofol sedation, 21 subjects)
02_preprocess.py     → Filter, downsample, ICA, epoch
03_compute_metrics.py → Classical metrics + persistent homology per epoch
04_temporal_ordering.py → The actual test: does topology drop first?
```

## Folder structure

This subproject is intended to be self-contained:

```
nft-tda-reanalysis/
├── 01_download.py
├── 02_preprocess.py
├── 03_compute_metrics.py
├── 04_temporal_ordering.py
├── run_pipeline.py
├── config.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   └── processed/
└── outputs/
    ├── results/
    └── figures/
```

`data/` and `outputs/` are created locally under this folder so the reanalysis
does not spill downloaded data and generated artifacts into the repo root.

## Setup

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

`giotto-tda` did not resolve under Python 3.14 on this machine, so Python 3.11
is the safer default for now.

## Running

Run the full pipeline:

```bash
python run_pipeline.py
```

Run from a later step:

```bash
python run_pipeline.py --from-step preprocess
```

Run a single step:

```bash
python run_pipeline.py --only ordering
```

## Key metrics

**Classical** (existing in literature):
- Band power (delta through gamma)
- Spectral edge frequency
- RMS amplitude
- Lempel-Ziv complexity
- Weighted phase lag index (alpha, gamma)

**Topological** (NFT-specific):
- Persistent homology of channel correlation matrices (Vietoris-Rips)
- Betti numbers β₀–β₃ (max, mean, AUC of Betti curves)
- Persistence entropy per homology dimension
- Total persistence per dimension
- Composite topological complexity score

## What a positive result looks like

During induction (awake → sedated): topological metrics show statistically
significant decline 2+ epochs before classical metrics do. Bootstrap CI on
the onset difference is entirely positive.

For DS005620 specifically, this is an acquisition-ordered proxy analysis:
awake EC baseline epochs are compared against later `sed` / `sed2` rest runs
ordered by `sub-*/sub-*_scans.tsv`. The dataset does not expose true induction
markers inside the rest recordings.

## What a negative result looks like

Topological and classical metrics decline simultaneously, or classical metrics
decline first. This is a legitimate falsification of the temporal ordering
prediction — report it honestly.

## Known limitations

- Channel-level TDA (correlation distance) is a coarse proxy for the
  simplicial complex structure Reimann et al. (2017) found in spike data.
  Ideally you'd want intracranial recordings, not scalp EEG.
- The dataset may not have fine-grained temporal resolution during the
  induction transition. If propofol was administered as a bolus, the
  transition window may be too fast to resolve ordering.
- The rest recordings contain start markers but not induction onsets, so this
  repo currently implements an acquisition-ordered proxy rather than a true
  within-transition changepoint analysis.
- β₃ and higher are computationally expensive and may not be meaningful
  with ~32 EEG channels (you need more points than dimensions).

## Dependencies

- mne (EEG processing)
- giotto-tda (persistent homology)
- numpy, scipy, pandas (computation)
- matplotlib, seaborn (figures)
- openneuro-py (data download)
- joblib (parallelization)
