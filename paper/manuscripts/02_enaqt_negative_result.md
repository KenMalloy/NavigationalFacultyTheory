# Testing Environment-Assisted Quantum Transport Under Physiological Constraints

## Title

Testing Environment-Assisted Quantum Transport Under Physiological Constraints: A Geometry-Informed Tryptophan-Network Baseline

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Negative-result simulation paper |
| Current status | Results-backed baseline draft; still needs tubulin-specific geometry ensembles for a full submission |
| Supports book material | `book_draft_v2.md` Chapter 8 |
| Best venue class | Biophysics, quantum biology, reproducibility-focused negative results |
| Core risk | Overclaiming from a geometry-informed baseline to full tubulin-specific generality |

## Abstract

This manuscript should test a narrow claim: whether environment-assisted quantum transport yields a transfer advantage once the system is pushed into a physiological dephasing regime. The strongest publishable version is a negative-result simulation paper, not a speculative consciousness paper. A fresh local run of `enaqt_simulation/phase2_transport.py` now provides a verified baseline result for the repo: in the default geometry-informed eight-site helix model, transport efficiency monotonically improves toward the coherent limit and does not exhibit an intermediate-noise ENAQT peak. The physiological regime is deeply dephasing-dominated, with `kappa_phys / V = 40.53` and effective `gamma/kappa = 0.0247`, well away from the coherent regime where efficiency is highest. That is enough to make this file substantially more concrete, while still stopping short of a full tubulin-specific submission claim.

## Study Question

The paper should answer one question only:

Does ENAQT produce a reproducible transport advantage once the model is evaluated in the same regime that living cells actually occupy?

Everything else should be subordinate to that.

## Verified Local Baseline Result

Fresh local verification used:

`PYTHONPATH=. ./.venv/bin/python enaqt_simulation/phase2_transport.py --ratio-count 20 --t-max-ps 20 --dt-ps 0.1`

The result for the default geometry-informed helix model was:

| Quantity | Verified local value |
| --- | --- |
| Sites | 8 |
| Median nearest-neighbor coupling `V` | `11.3019 rad/ps` |
| Physiological dephasing `kappa_phys` | `458.0596 ps^-1` |
| `kappa_phys / V` | `40.5294` |
| Equivalent physiological `gamma/kappa` | `0.0247` |
| Max transport efficiency | `0.3841` at `gamma/kappa = 1000` |
| Efficiency near physiological regime | about `0.327` |
| Verdict | no ENAQT; efficiency highest in coherent regime |

The most important sentence this enables is simple and publishable: in the verified local baseline model, dephasing does not enhance transport.

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

- the repo's baseline transport model can be reproduced
- the physiological regime in that model is strongly dephasing-dominated
- the local baseline does not produce an ENAQT window

It does not yet show:

- that all tubulin-derived geometries behave this way
- that sink-placement uncertainty or structural perturbations have already been exhausted
- that the negative result is independent of model class

## What Is Already In This Repo

- `enaqt_simulation/phase2_transport.py` contains the transport sweep logic and ENAQT detection criteria.
- `enaqt_simulation/core.py` contains the Hamiltonian and Liouvillian building blocks used by the sweep.
- `book_draft_v2.md` already captures the intended headline that the excitonic route failed under physiological conditions.

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

- the excitonic mechanism was worth testing
- the test was failed honestly
- the failure is informative because it narrows the viable mechanism search
- the current repo already contains one verified negative baseline even before the full structural sweep is assembled

It is weakest if it tries to convert a transport paper into a consciousness paper.

## Data and Code Availability

The paper should ship with:

- the exact sweep script
- raw CSV outputs for every parameter sweep cited in the manuscript
- a container or locked environment file
- one appendix table mapping each parameter to its source or rationale

## Submission Blockers

- Add tubulin-specific geometry families rather than relying on the geometry-informed helix baseline alone.
- Export the actual sweep outputs used for the negative-result claim into manuscript tables.
- Add a parameter-justification table and separate literature-constrained values from exploratory priors.
- Keep the title and abstract honest about the current scope until the structural ensemble is complete.
