# Radical-Pair Spin Effects as a Candidate Modulator of Tubulin Dynamics

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Mechanistic feasibility paper with quantitative bottleneck analysis |
| Current status | Quantitatively grounded draft with freshly verified local results, but still too chemistry-light for direct submission |
| Supports book material | `book_draft_v2.md` Chapters 8 and 9 |
| Best venue class | Quantum biology, spin chemistry, mechanistic biophysics |
| Core risk | Overstating tubulin-specific biochemical certainty when the local model is still a minimal radical-pair model |

## Abstract

This paper should be framed as a feasibility and bottleneck analysis, not as proof that tubulin radical pairs implement consciousness. The local repo already contains enough ingredients to support a serious draft. A fresh local run of `enaqt_simulation/spin_coherence.py` using the repo's `.venv` verifies microsecond-scale coherence and a large quantum-classical chemical divergence in the minimal Haberkorn model. At Earth-strength field, the quantum and classical trajectories diverge for the full `10 us` simulation window, the quantum coherence lifetime is `1.480 us`, and the singlet-yield shift relative to the classical baseline has magnitude `12.69%`. A separate transduction-chain analysis in `enaqt_simulation/transduction_chain_results.md` shows that this microscale effect is not obviously fatal but becomes bottlenecked by radical-pair formation rate: under conservative assumptions the resulting neural-scale signal falls roughly one order of magnitude below thermal noise, while more favorable superoxide and microtubule-count assumptions close that gap. That makes the strongest publishable paper a disciplined feasibility study with explicit kill conditions, not a solved mechanism paper.

## Current Evidence In This Repo

| Local artifact | What it contributes | What it does not settle |
| --- | --- | --- |
| `enaqt_simulation/spin_coherence.py` | minimal radical-pair model, yield difference, field sensitivity, coherence lifetime | actual tubulin chemical identity and parameter realism |
| `enaqt_simulation/criticality_amplification.py` | demonstration that tiny microscale biases can be amplified near criticality | whether microtubules instantiate that exact amplification pathway |
| `enaqt_simulation/transduction_chain.py` and `enaqt_simulation/transduction_chain_results.md` | explicit bottleneck map from radical pair to neural-scale signal | empirical values for local ROS, coupling efficiency, and effective microtubule count |

## Freshly Verified Local Results

Using `./.venv/bin/python enaqt_simulation/spin_coherence.py`, the repo currently reports:

| Quantity | Verified local value |
| --- | --- |
| Quantum coherence lifetime at Earth field | `1.480 us` |
| Classical coherence lifetime | `0.470 us` |
| Quantum singlet yield at Earth field | `0.797114` |
| Classical singlet yield at Earth field | `0.913009` |
| Singlet-yield shift magnitude | `12.69%` |
| Trajectory divergence duration | `10.000 us` |
| Yield change from zero field to Earth field | `-1.4577%` |

Using `./.venv/bin/python enaqt_simulation/criticality_amplification.py`, the repo also reports:

| Quantity | Verified local value |
| --- | --- |
| Microscale bias tested | `epsilon = 0.002` |
| Amplification at subcritical `sigma = 0.90` | `+3.63%` |
| Amplification at critical `sigma = 1.00` | `+10.24%` |
| Amplification at supercritical `sigma = 1.05` | `+6.03%` |
| Critical versus subcritical amplification ratio | `2.8x` |

These numbers do not prove a biological mechanism, but they do make the paper much harder to dismiss as purely rhetorical.

## Quantitative Bottleneck Map

Source: `enaqt_simulation/transduction_chain_results.md`

| Quantity | Conservative local value | Interpretation |
| --- | --- | --- |
| Quantum-classical yield shift magnitude | 12.69% | microscale signal is nontrivial |
| Radical pair events per neuron in 5 ms | about 10 | main bottleneck under conservative assumptions |
| Equivalent voltage shift | `9.9 x 10^-3 mV` | roughly one order below `0.1 mV` neural noise scale |
| Amplified firing bias | `3.4 x 10^-2` | potentially meaningful if upstream rate assumptions improve |
| Dominant swing factor | local superoxide concentration | gating variable for viability |

## Interpretation

The current local evidence supports a specific and limited claim. Radical-pair dynamics are a far better mechanistic candidate than the discarded excitonic route because they operate on microsecond rather than femtosecond-to-picosecond scales, produce a nontrivial chemical outcome difference, and remain field-sensitive. But the transduction problem remains real. The repo's own bottleneck analysis says the mechanism fails if event rate never rises above the conservative baseline.

## What The Paper Can Say Right Now

- a minimal radical-pair model produces a measurable quantum-classical chemical difference
- that difference persists on timescales dramatically longer than the discarded excitonic route
- the transduction chain is thin but not obviously dead
- the viability hinge is event rate, not the existence of a microscale quantum signal

## What The Paper Cannot Say Yet

- it cannot identify the tubulin radical pair with biochemical specificity
- it cannot claim that the effect is already linked to cognition
- it cannot claim that the current transduction chain is empirically validated rather than order-of-magnitude constrained

## Alternative Explanations The Paper Must Engage

- field or isotope effects in tubulin-related assays may reflect generic redox chemistry rather than access-relevant signaling
- any tubulin polymerization effect could be structural or pharmacological without requiring a consciousness link
- amplification in an abstract branching network does not by itself demonstrate amplification in a real cytoskeletal-neural pathway

## Recommended Manuscript Spine

1. Radical-pair mechanism and why it is the right quantum-biology comparison class.
2. Minimal model and parameter choices.
3. Quantitative bottleneck table.
4. Alternative non-spin explanations and why they remain live.
5. Kill conditions and next experiments.

## Minimal Kill Conditions

The paper becomes stronger if it says in advance what would weaken it.

- no radical-pair-compatible chemistry can be identified in tubulin
- realistic local ROS exposure is far below the rate needed to accumulate events in a neural integration window
- radical-pair products fail to couple measurably to tubulin conformational dynamics

## Data and Code Availability

Submission should include:

- the spin-coherence script
- the transduction-chain script and result markdown
- the criticality amplification script and summary outputs
- one parameter table separating literature-backed values from exploratory ranges

## Submission Blockers

- Replace generic “tubulin radical pair” language with either a named candidate chemical route or an explicit placeholder statement.
- Add an alternatives section for non-spin explanations of tubulin field or isotope effects.
- Finalize which numbers are directly reported from code versus imported from the book narrative.
- Remove any prose that sounds like a solved neural mechanism rather than a constrained feasibility analysis.
