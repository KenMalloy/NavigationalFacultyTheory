# Topological Features Did Not Precede Classical EEG Markers in an Acquisition-Ordered Propofol Proxy Reanalysis

## Title

Topological Features Did Not Precede Classical EEG Markers in an Acquisition-Ordered Propofol Proxy Reanalysis

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Negative-result reanalysis paper |
| Current status | Results-backed standalone draft with an explicit acquisition-ordered proxy limitation in the abstract, methods, and conclusion |
| Supports book material | `book_draft_v2.md` Chapter 13 |
| Best venue class | Neuroinformatics, EEG methods, negative results, consciousness methodology |
| Core risk | Overselling temporal-ordering claims when the dataset supports only an acquisition-ordered proxy analysis |

## Abstract

This manuscript is strongest as a careful reanalysis paper, not as a sweeping claim about topology in consciousness. The local pipeline in `nft-tda-reanalysis/` computes both classical EEG features (Lempel-Ziv complexity, [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532); alpha-band weighted phase lag index, [Vinck et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21276857/)) and persistent-homology-derived topological metrics on the public propofol dataset [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0). **Important limitation: the analysis is an acquisition-ordered proxy because ds005620 does not expose true induction timing inside the rest recordings.** The current summary statistic file `results/temporal_ordering_stats.csv` does not support the topology-first prediction. Against both comparators, the median lead-lag difference is strongly negative, the estimated proportion of subjects showing topology-first ordering is low, and the local `nft_supported` flag is `False`. Topological features did not precede classical markers in this acquisition-ordered proxy reanalysis. This weakens a specific ordering prediction; it does not establish that topological features are uninformative for EEG analysis in general. The paper becomes publishable by being precise: this is an acquisition-ordered proxy analysis that weakens a specific prediction, not the final word on topology and anesthesia.

## Methods As Currently Implemented

The existing pipeline already gives this manuscript a reproducible backbone. All analyses operate on the public propofol dataset [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0).

| Step | Local implementation |
| --- | --- |
| Data download | `nft-tda-reanalysis/01_download.py` |
| EEG preprocessing | `nft-tda-reanalysis/02_preprocess.py` |
| Feature computation | `nft-tda-reanalysis/03_compute_metrics.py` (Lempel-Ziv complexity per [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532); alpha-band wPLI per [Vinck et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21276857/); persistent homology for topological features) |
| Ordering test | `nft-tda-reanalysis/04_temporal_ordering.py` |
| End-to-end runner | `nft-tda-reanalysis/run_pipeline.py` |

**Proxy limitation.** The analysis is an acquisition-ordered proxy because ds005620 does not expose true induction timing inside the rest recordings. All temporal ordering comparisons use the sequence of awake, `sed`, and `sed2` runs as a surrogate for true propofol induction onset.

## Current Result Summary

Source: `results/temporal_ordering_stats.csv`

| Classical comparator | n subjects | Median diff epochs | Interval | p value | Topology-first proportion | NFT supported |
| --- | --- | --- |
| Lempel-Ziv | 17 | -57.0 | [-102.0, 0.0] | 0.9579 | 0.1176 | False |
| wPLI alpha | 18 | -59.5 | [-84.0, -21.9250] | 0.9984 | 0.1111 | False |

These rows are enough to support a negative-result manuscript if the paper is explicit that the ordering variable is acquisition order rather than a directly observed induction timeline.

## Primary Interpretation

The right interpretation is narrower than the original book-level claim.

- topological features did not precede classical markers in this acquisition-ordered proxy reanalysis; the tested topology-first prediction is not supported in this dataset under this design
- the negative result is directional, not merely null, because the median differences are negative
- the claim being weakened is specifically an ordering claim, not the broader usefulness of topological features in EEG analysis; TDA may still be informative for consciousness research through other analytic designs or datasets

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
- the current dataset ([OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0)) does not expose true induction onsets inside the rest recordings; all temporal ordering is therefore acquisition-ordered, not induction-timed
- the present analysis is therefore a disciplined proxy test rather than a definitive induction-timed analysis
- even under that limitation, topological features did not precede classical markers in this acquisition-ordered proxy reanalysis
- this weakens the ordering claim specifically; it does not establish that topology is uninformative for consciousness-related EEG analysis in general

## Primary Methods Commitments

The single-file draft should lock these choices in the manuscript body.

| Item | Primary choice |
| --- | --- |
| Dataset | [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0) |
| Primary topology representation | channel-correlation persistent homology (see [Reimann et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467434/) for neural-topology motivation; note that scalp-EEG persistent homology is only a coarse proxy for the circuit-level topology described in that work) |
| Primary classical comparators | Lempel-Ziv complexity ([Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532)) and alpha-band wPLI ([Vinck et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21276857/)) |
| Ordering variable | acquisition order across awake, `sed`, and `sed2` runs |
| Primary outcome | whether topology declines before classical comparators |

Secondary analyses can exist, but they should be labeled secondary.

## What Would Strengthen The Paper Further

- a second dataset with better induction timing
- a locked robustness hierarchy for alternative TDA summaries
- explicit subject-level models in the manuscript appendix rather than only in code

## Honest Interpretation

This paper should not say topology is useless or that topological features never precede classical markers. It should say that a specific ordering prediction did not survive a specific acquisition-ordered proxy test in a single public dataset. That is scientifically valuable because the prediction was directional and discriminative, and the negative result is reported honestly against the theory's own prior commitment. The proxy limitation -- that ds005620 does not expose true induction timing inside the rest recordings -- is a methodological constraint, not a reason to discount the result. It simply means that a future analysis with direct induction timing could either confirm or reverse this finding.

## Data and Code Availability

This is one of the easiest papers in the portfolio to make reproducible.

- source dataset: [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0)
- code already exists in `nft-tda-reanalysis/`
- output tables already exist in `results/`
- figures already exist in `figures/`

## Submission Blockers

- ~~Add one paragraph in the abstract and one in the discussion clarifying the acquisition-ordered proxy design.~~ Done: proxy limitation now appears in abstract, methods, "What The Paper Should Say Carefully", and "Honest Interpretation" sections.
- Lock one primary TDA representation and label all others robustness checks.
- Add the subject-level statistical model and robustness plan directly to the manuscript.
- ~~Finalize the bibliography~~ Partially done: dataset DOI, Schartner et al. 2015, Vinck et al. 2011, and Reimann et al. 2017 now cited. Remaining: convert the remaining draft prose into journal-native language.
- Re-run the pipeline in a pinned environment before submission and archive the exact environment file.
