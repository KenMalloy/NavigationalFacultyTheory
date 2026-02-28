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
01_download.py       → Fetch OpenNeuro DS005620 (propofol sedation, 21 subjects)
02_preprocess.py     → Filter, downsample, ICA, epoch
03_compute_metrics.py → Classical metrics + persistent homology per epoch
04_temporal_ordering.py → The actual test: does topology drop first?
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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
- Event markers need to be inspected and mapped to the STATES config
  before results are interpretable.
- β₃ and higher are computationally expensive and may not be meaningful
  with ~32 EEG channels (you need more points than dimensions).

## Dependencies

- mne (EEG processing)
- giotto-tda (persistent homology)
- numpy, scipy, pandas (computation)
- matplotlib, seaborn (figures)
- openneuro-py (data download)
- joblib (parallelization)
