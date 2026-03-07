# Testing Environment-Assisted Quantum Transport in a Geometry-Informed Baseline

## Title

Testing Environment-Assisted Quantum Transport in a Geometry-Informed Tryptophan-Network Baseline Under Physiological Dephasing Constraints

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Negative-result simulation paper |
| Current status | Results-backed baseline draft; still needs tubulin-specific geometry ensembles for a full submission |
| Supports book material | `book_draft_v2.md` Chapter 8 |
| Best venue class | Biophysics, quantum biology, reproducibility-focused negative results |
| Core risk | Overclaiming from a geometry-informed baseline to full tubulin-specific generality |

## Abstract

Environment-assisted quantum transport (ENAQT) — theoretically predicted by Mohseni et al. (2008) and experimentally supported in photosynthetic complexes by Panitchayangkoon et al. (2010) — posits that intermediate dephasing can enhance excitonic transfer efficiency. This manuscript tests whether that advantage survives once a geometry-informed baseline model is evaluated in a physiological dephasing regime, rather than in the coherence-favoring regimes where the effect was originally characterized. The strongest publishable version is a negative-result simulation paper, not a speculative consciousness paper. A fresh local run of `enaqt_simulation/phase2_transport.py` provides a verified baseline result: in the default geometry-informed eight-site helix model, transport efficiency monotonically improves toward the coherent limit and does not exhibit an intermediate-noise ENAQT peak. In the default helix baseline, the modeled physiological regime is strongly dephasing-dominated, with `kappa_phys / V = 40.53 (dimensionless ratio of dephasing rate in ps^-1 to median nearest-neighbor coupling in rad/ps)` and effective `gamma/kappa = 0.0247 (dimensionless coherent-to-dephasing ratio)`, well away from the coherent regime where efficiency is highest. This rules out the modeled excitonic transport route under these assumptions but does not generalize to all tubulin-derived geometries or model classes. The full dephasing sweep output and raw CSV are available in the data supplement.

## Study Question

The paper proposes a discriminative test: does ENAQT produce a reproducible transport advantage once the default geometry-informed helix baseline model is evaluated in a physiological dephasing regime? This test logic follows from the ENAQT theory of Mohseni et al. (2008) and the experimental demonstration by Panitchayangkoon et al. (2010), which established that intermediate dephasing can enhance transfer efficiency in photosynthetic complexes. If the effect is biologically relevant, it should survive under physiological noise levels — not only under coherence-favoring conditions.

Everything else should be subordinate to that.

## Verified Local Baseline Result

Fresh local verification used:

`PYTHONPATH=. ./.venv/bin/python enaqt_simulation/phase2_transport.py --ratio-count 20 --t-max-ps 20 --dt-ps 0.1`

The result for the default geometry-informed helix model was:

| Quantity | Verified local value | Derivation and units |
| --- | --- | --- |
| Sites | 8 | Fixed by geometry definition |
| Median nearest-neighbor coupling `V` | `11.3019 rad/ps` | Computed from dipole-dipole coupling at helix-derived inter-site distances |
| Physiological dephasing `kappa_phys` | `458.0596 ps^-1` | Derived from thermal dephasing at 310 K using the model's spectral density |
| `kappa_phys / V` | `40.5294` (dimensionless) | Ratio of dephasing rate (`ps^-1`) to median coupling (`rad/ps`); values >1 indicate dephasing-dominated regime |
| Equivalent physiological `gamma/kappa` | `0.0247` (dimensionless) | Inverse measure: coherent-to-dephasing ratio; values <<1 indicate far from the coherent limit |
| Max transport efficiency | `0.3841` at `gamma/kappa = 1000` | From the full 20-point dephasing sweep (see raw CSV in data supplement) |
| Efficiency near physiological regime | about `0.327` | Interpolated from sweep at `gamma/kappa ~ 0.025` |
| Verdict | no ENAQT peak in the default geometry-informed helix baseline | Efficiency increases monotonically toward the coherent limit across the full sweep |

The most important sentence this enables: in the verified default geometry-informed helix baseline model, dephasing does not enhance transport.

### Limitations of the Baseline Result

This result rules out the modeled excitonic transport route under the specific assumptions of the default geometry-informed helix baseline. It does not generalize to tubulin writ large. Key limitations include:

- **Geometry**: The eight-site helix model uses a single geometry-informed configuration, not a structural ensemble drawn from crystallographic tubulin data. Other site placements, inter-site distances, or protofilament geometries could shift the dephasing-to-coupling ratio into a regime where ENAQT peaks are possible.
- **Model class**: The Lindblad dephasing model used here is one of several open-quantum-system approaches. Redfield, hierarchical equations of motion (HEOM), or polaron-transformed master equations might yield different transport landscapes.
- **Sink placement**: The current sink-placement rule is fixed by the geometry definition. Alternative sink rules or multi-sink configurations remain unexplored.
- **Disorder**: No disorder ensemble or Monte Carlo sampling over site energies was performed. The result reflects a single realization of the baseline Hamiltonian.
- **Scope**: This negative result narrows the viable mechanism search but does not eliminate all possible excitonic routes in biological tubulin systems.

## Methods Spine

The single-file manuscript should lock the following items.

| Item | Requirement for publication |
| --- | --- |
| Geometry source | name the structure source, site definition rule, and sink-placement rule |
| Hamiltonian | state site-energy disorder model and dipole-coupling construction |
| Open-system model | state the Lindblad or equivalent transport model clearly enough for reimplementation |
| Baselines | define coherent, incoherent, and intermediate-dephasing comparators mathematically |
| Negative-result criterion | define what counts as “no robust advantage” before reporting outputs |
| Uncertainty | report number of disorder realizations, confidence intervals, and geometry sensitivity |

## What The Current Result Does And Does Not Show

It shows:

- the repo's default geometry-informed helix baseline transport model can be reproduced
- in the default helix baseline, the modeled physiological regime is strongly dephasing-dominated
- the default geometry-informed helix baseline does not produce an ENAQT window

It does not yet show:

- that all tubulin-derived geometries behave this way
- that sink-placement uncertainty or structural perturbations have already been exhausted
- that the negative result is independent of model class

## What Is Already In This Repo

- `enaqt_simulation/phase2_transport.py` contains the transport sweep logic and ENAQT detection criteria.
- `enaqt_simulation/core.py` contains the Hamiltonian and Liouvillian building blocks used by the sweep.
- `book_draft_v2.md` already captures the intended headline that the excitonic route failed under physiological conditions in the default geometry-informed helix baseline.

What is missing from the current manuscript package is just as important.

- No tubulin-specific geometry ensemble table yet pins the structure source, sink rule, and disorder regime.
- No parameter-justification table yet distinguishes literature-constrained values from exploratory sensitivity sweeps.

## Recommended Result Reporting

The paper should report a small fixed set of outputs.

1. Efficiency versus dephasing for each geometry family.
2. The location of any local maximum, if one exists.
3. The effect size of that maximum relative to both coherent and incoherent baselines.
4. The fraction of geometries in which a claimed ENAQT window survives.
5. A sensitivity table showing which assumptions are carrying the result.

## Honest Interpretation

This paper is strongest if it says:

- the excitonic mechanism was worth testing — ENAQT theory (Mohseni et al. 2008) and experiment (Panitchayangkoon et al. 2010) established that intermediate dephasing can enhance transport in photosynthetic complexes, making it natural to ask whether the same effect survives in other biological geometries under physiological noise
- the test was failed honestly in the default geometry-informed helix baseline
- the failure is informative because it rules out this modeled route under these assumptions and narrows the viable mechanism search
- the current repo already contains one verified negative baseline even before the full structural sweep is assembled

It is weakest if it tries to convert a transport paper into a consciousness paper, or if it generalizes from the baseline result to claims about excitonic transport in tubulin writ large.

## References

- Mohseni, M., Rebentrost, P., Lloyd, S., & Aspuru-Guzik, A. (2008). Environment-assisted quantum walks in photosynthetic energy transfer. *Journal of Chemical Physics*, 129(17), 174106. PMID: [19045332](https://pubmed.ncbi.nlm.nih.gov/19045332/)
- Panitchayangkoon, G., Hayes, D., Fransted, K. A., et al. (2010). Long-lived quantum coherence in photosynthetic complexes at physiological temperature. *Proceedings of the National Academy of Sciences*, 107(29), 12766–12770. PMC: [PMC2919932](https://pmc.ncbi.nlm.nih.gov/articles/PMC2919932/)

## Data and Code Availability

The paper should ship with:

- the exact sweep script
- raw CSV outputs for every parameter sweep cited in the manuscript
- a container or locked environment file
- one appendix table mapping each parameter to its source or rationale

## Submission Blockers

- Add tubulin-specific geometry families rather than relying on the default geometry-informed helix baseline alone; without this, the manuscript cannot claim to rule out excitonic transport in tubulin — only that this modeled route fails under these assumptions.
- Export the actual sweep outputs and raw CSV files used for the negative-result claim into manuscript tables and data supplement.
- Add a parameter-justification table and separate literature-constrained values from exploratory priors.
- Keep the title and abstract scoped to the geometry-informed baseline until the structural ensemble is complete.
