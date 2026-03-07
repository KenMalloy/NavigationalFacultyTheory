# Topological Features Do Not Precede Classical EEG Markers in an Acquisition-Ordered Propofol Reanalysis

## Title

Topological Features Do Not Precede Classical EEG Markers in an Acquisition-Ordered Propofol Reanalysis

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Negative-result reanalysis paper |
| Current status | Results-backed standalone draft with a clear caution about dataset timing limits |
| Supports book material | `book_draft_v2.md` Chapter 13 |
| Best venue class | Neuroinformatics, EEG methods, negative results, consciousness methodology |
| Core risk | Overselling temporal-ordering claims when the dataset supports only an acquisition-ordered proxy analysis |

## Abstract

This manuscript is strongest as a careful reanalysis paper, not as a sweeping claim about topology in consciousness. The local pipeline in `nft-tda-reanalysis/` already computes both classical EEG features and persistent-homology-derived metrics on the public propofol dataset `ds005620`. The current summary statistic file `results/temporal_ordering_stats.csv` does not support the topology-first prediction. Against both Lempel-Ziv complexity and alpha-band weighted phase lag index, the median lead-lag difference is strongly negative, the estimated proportion of subjects showing topology-first ordering is low, and the local `nft_supported` flag is `False`. The paper becomes publishable by being precise: this is an acquisition-ordered proxy analysis that weakens a specific prediction, not the final word on topology and anesthesia.

## Methods As Currently Implemented

The existing pipeline already gives this manuscript a reproducible backbone.

| Step | Local implementation |
| --- | --- |
| Data download | `nft-tda-reanalysis/01_download.py` |
| EEG preprocessing | `nft-tda-reanalysis/02_preprocess.py` |
| Feature computation | `nft-tda-reanalysis/03_compute_metrics.py` |
| Ordering test | `nft-tda-reanalysis/04_temporal_ordering.py` |
| End-to-end runner | `nft-tda-reanalysis/run_pipeline.py` |

The current README also makes the most important limitation explicit: this is an acquisition-ordered proxy analysis because the dataset does not expose true induction markers inside the rest recordings.

## Current Result Summary

Source: `results/temporal_ordering_stats.csv`

| Classical comparator | n subjects | Median diff epochs | Interval | p value | Topology-first proportion | NFT supported |
| --- | --- | --- |
| Lempel-Ziv | 17 | -57.0 | [-102.0, 0.0] | 0.9579 | 0.1176 | False |
| wPLI alpha | 18 | -59.5 | [-84.0, -21.9250] | 0.9984 | 0.1111 | False |

These rows are enough to support a negative-result manuscript if the paper is explicit that the ordering variable is acquisition order rather than a directly observed induction timeline.

## Primary Interpretation

The right interpretation is narrower than the original book-level claim.

- the tested topology-first prediction is not supported in this dataset
- the negative result is directional, not merely null, because the median differences are negative
- the claim being weakened is specifically an ordering claim, not the broader usefulness of topological features in EEG analysis

## What The Pipeline Already Provides

- `nft-tda-reanalysis/run_pipeline.py` for end-to-end orchestration
- `01_download.py` through `04_temporal_ordering.py` for a reproducible BIDS-to-stats path
- subject-level metrics in `results/`
- summary figures in `figures/`

## Recommended Main-Figure Story

The paper's main figure sequence should be simple.

1. Dataset and acquisition-order schematic.
2. Subject-level lead-lag distribution for primary comparators.
3. Group-level summary table for topology-first versus classical-first ordering.

That is enough for a publishable negative-result paper if the text does not drift into over-interpretation.

## What The Paper Should Say Carefully

- the tested prediction was a topology-first ordering claim
- the current dataset does not expose true induction onsets inside the rest recordings
- the present analysis is therefore a disciplined proxy test rather than a definitive induction-timed analysis
- even under that limitation, the local evidence does not support the claimed topology lead

## Primary Methods Commitments

The single-file draft should lock these choices in the manuscript body.

| Item | Primary choice |
| --- | --- |
| Dataset | OpenNeuro `ds005620` |
| Primary topology representation | channel-correlation persistent homology |
| Primary classical comparators | Lempel-Ziv and alpha-band wPLI |
| Ordering variable | acquisition order across awake, `sed`, and `sed2` runs |
| Primary outcome | whether topology declines before classical comparators |

Secondary analyses can exist, but they should be labeled secondary.

## What Would Strengthen The Paper Further

- a second dataset with better induction timing
- a locked robustness hierarchy for alternative TDA summaries
- explicit subject-level models in the manuscript appendix rather than only in code

## Honest Interpretation

This paper should not say topology is useless. It should say that this specific claim did not survive this specific test. That is scientifically valuable because the prediction was directional and discriminative.

## Data and Code Availability

This is one of the easiest papers in the portfolio to make reproducible.

- code already exists in `nft-tda-reanalysis/`
- output tables already exist in `results/`
- figures already exist in `figures/`

## Submission Blockers

- Add one paragraph in the abstract and one in the discussion clarifying the acquisition-ordered proxy design.
- Lock one primary TDA representation and label all others robustness checks.
- Add the subject-level statistical model and robustness plan directly to the manuscript.
- Finalize the bibliography and convert the remaining draft prose into journal-native language.
