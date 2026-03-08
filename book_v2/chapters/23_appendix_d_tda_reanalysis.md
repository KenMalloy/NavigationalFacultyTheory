## Appendix D: TDA Reanalysis — Methods and Results

NFT makes a specific temporal ordering prediction: topological complexity of neural dynamics should decline before classical activity metrics during anesthetic induction. We tested this prediction against a public propofol dataset. The topology did not lead.

### Dataset

We used OpenNeuro DS005620, a propofol sedation study with 21 subjects. Each subject has resting-state EEG recordings in awake, sedated, and deeply sedated conditions. The dataset is BIDS-compliant and publicly available.

A critical limitation: DS005620 does not expose true propofol induction timing within the rest recordings. We use the acquisition order of the recording runs as a proxy for the induction trajectory. Every result that follows should be read with this constraint in mind.

### Pipeline

The analysis pipeline consists of four stages, all available in the project repository:

1. **Download** (01_download.py): Fetches raw data from OpenNeuro.
2. **Preprocessing** (02_preprocess.py): Band-pass filtering, downsampling, ICA-based artifact rejection, and epoching.
3. **Feature computation** (03_compute_metrics.py): Computes both classical and topological features per epoch.
4. **Temporal ordering test** (04_temporal_ordering.py): Does topology decline first?

### Features Computed

**Classical comparators.** Two established consciousness-sensitive metrics: Lempel-Ziv complexity (following Schartner et al. 2015) and alpha-band weighted phase lag index (wPLI, following Vinck et al. 2011).

**Topological features.** Persistent homology of channel-correlation matrices using a Vietoris-Rips filtration, yielding Betti numbers, persistence entropy, total persistence per homological dimension, and a composite topological complexity score.

### Results

| Comparator | n | Median lag (epochs) | p-value | Topology-first proportion |
|---|---|---|---|---|
| Lempel-Ziv | 17 | −57.0 | 0.958 | 0.12 |
| Alpha wPLI | 18 | −59.5 | 0.998 | 0.11 |

Against both comparators, classical metrics declined first by a wide margin. Only 11–12% of subjects showed topology-first ordering — consistent with chance. The prediction is not supported.

The result is directional, not merely null. Topological features did not just fail to lead — they consistently lagged behind classical markers. A future dataset with marked induction onsets within continuous recordings could confirm or reverse this finding.

---

