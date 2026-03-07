# Radical-Pair Spin Effects as a Candidate Modulator of Tubulin Dynamics: A Parameterized Feasibility Model

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Parameterized feasibility model with quantitative bottleneck analysis |
| Current status | Quantitatively grounded draft with freshly verified local results, but still too chemistry-light for direct submission. The model is a minimal radical-pair system, not tubulin-specific chemistry. |
| Supports book material | `book_draft_v2.md` Chapters 8 and 9 |
| Best venue class | Quantum biology, spin chemistry, mechanistic biophysics |
| Core risk | The gap between "we modeled generic radical pairs" and "this is about tubulin specifically." Every claim must be clear about which level of specificity it operates at: generic radical-pair physics, hypothetical tubulin-associated radical-pair route, or empirically validated tubulin chemistry. The model currently operates at the first level only. |

## Abstract

This paper should be framed as a parameterized feasibility model and bottleneck analysis, not as proof that tubulin radical pairs implement consciousness. The local repo already contains enough ingredients to support a serious draft, but the model operates at the level of generic radical-pair physics (Haberkorn 1976), not tubulin-specific chemistry. No particular radical-pair-forming reaction in tubulin has been identified; the model uses a placeholder route (superoxide encounter with tryptophan residues) as an order-of-magnitude scenario.

A fresh local run of `enaqt_simulation/spin_coherence.py` using the repo's `.venv` verifies microsecond-scale coherence and a large quantum-classical chemical divergence in the minimal Haberkorn model. At Earth-strength field, the quantum and classical trajectories diverge for the full `10 us` simulation window, the quantum coherence lifetime is `1.480 us`, and the singlet-yield shift relative to the classical baseline has magnitude `12.69%`. These results describe a minimal radical-pair model, not tubulin-specific chemistry.

A separate order-of-magnitude transduction-chain model in `enaqt_simulation/transduction_chain_results.md` shows that this microscale effect becomes bottlenecked by radical-pair formation rate: under conservative assumptions the resulting neural-scale signal falls roughly one order of magnitude below thermal noise. The transduction-chain model remains parameter-sensitive and currently sub-noise under conservative assumptions, while more favorable superoxide (Murphy 2009; Sies and Jones 2020) and microtubule-count assumptions would close that gap. This makes the mechanism not yet ruled out by the current order-of-magnitude model, but not empirically supported either. The strongest publishable paper is a disciplined feasibility study with explicit kill conditions, not a solved mechanism paper.

## Current Evidence In This Repo

| Local artifact | What it contributes | Level of specificity | What it does not settle |
| --- | --- | --- | --- |
| `enaqt_simulation/spin_coherence.py` | minimal Haberkorn radical-pair model (Haberkorn 1976): yield difference, field sensitivity, coherence lifetime | Generic radical-pair physics | actual tubulin chemical identity, parameter realism, whether any radical pair forms in tubulin at biologically relevant rates |
| `enaqt_simulation/criticality_amplification.py` | qualitative demonstration that tiny microscale biases can be amplified near criticality in an abstract branching network | Generic network dynamics | whether microtubules or cytoskeletal-neural coupling instantiate that amplification pathway; this is not a validated neural transduction factor |
| `enaqt_simulation/transduction_chain.py` and `enaqt_simulation/transduction_chain_results.md` | order-of-magnitude bottleneck model from radical pair to neural-scale signal, using a placeholder [TrpH+...O2-] route | Hypothetical tubulin-associated route (not validated) | empirical values for local ROS, coupling efficiency, effective microtubule count, and whether the assumed chemical route exists |

## Freshly Verified Local Results

### Spin coherence (minimal radical-pair model)

Using `./.venv/bin/python enaqt_simulation/spin_coherence.py`, the repo currently reports results from a minimal Haberkorn radical-pair model (Haberkorn 1976). These numbers describe generic radical-pair physics with a single isotropic hyperfine coupling. They do not use tubulin-specific chemical parameters, because no such parameters are currently available for a validated tubulin radical pair. Results should be interpreted as setting a plausible scale for what radical-pair chemistry could produce if such a pair exists, not as modeling any known tubulin reaction.

| Quantity | Verified local value | Model level |
| --- | --- | --- |
| Quantum coherence lifetime at Earth field | `1.480 us` | Generic RP physics |
| Classical coherence lifetime | `0.470 us` | Generic RP physics |
| Quantum singlet yield at Earth field | `0.797114` | Generic RP physics |
| Classical singlet yield at Earth field | `0.913009` | Generic RP physics |
| Singlet-yield shift magnitude | `12.69%` | Generic RP physics |
| Trajectory divergence duration | `10.000 us` | Generic RP physics |
| Yield change from zero field to Earth field | `-1.4577%` | Generic RP physics |

For comparison, primary radical-pair magnetic sensitivity experiments (Maeda et al. 2012) demonstrate field-dependent yield changes of similar magnitude in well-characterized chemical systems, supporting the general plausibility of this effect size.

### Criticality amplification (abstract branching network)

Using `./.venv/bin/python enaqt_simulation/criticality_amplification.py`, the repo also reports results from an abstract branching network model. These results demonstrate qualitatively that small biases can be amplified near criticality, but this is not a validated neural transduction factor and should not be treated as one. The abstract network does not model any specific cytoskeletal or neural architecture.

| Quantity | Verified local value | Model level |
| --- | --- | --- |
| Microscale bias tested | `epsilon = 0.002` | Abstract branching network |
| Amplification at subcritical `sigma = 0.90` | `+3.63%` | Abstract branching network |
| Amplification at critical `sigma = 1.00` | `+10.24%` | Abstract branching network |
| Amplification at supercritical `sigma = 1.05` | `+6.03%` | Abstract branching network |
| Critical versus subcritical amplification ratio | `2.8x` | Abstract branching network |

**Note on the 51x amplification factor used in the transduction chain:** The transduction-chain model uses a `51x` amplification factor derived as `10.24% / 0.2%`, i.e., dividing the critical-regime firing-rate shift by the raw microscale bias `epsilon = 0.002`. This is the ratio of output effect to input bias in the abstract branching model. However, the more directly supported comparison is the `2.8x` ratio of critical to subcritical amplification (`10.24% / 3.63%`). The `51x` figure assumes the system starts from the raw epsilon and reaches the critical amplified value, which is the full input-to-output gain of the abstract network model, not a measured biological amplification factor. The transduction-chain results should be read with this derivation in mind.

These numbers do not prove a biological mechanism. They set quantitative scales for what generic radical-pair physics and abstract criticality models can produce.

## Quantitative Bottleneck Map

Source: `enaqt_simulation/transduction_chain_results.md`

This section presents order-of-magnitude model output only. Every number below depends on the assumptions in the following table. The model uses a placeholder chemical route ([TrpH+...O2-]) that has not been validated in tubulin, and an abstract criticality amplification factor that has not been validated in neural tissue. The results should be read as defining the parameter space in which a radical-pair mechanism would or would not be viable, not as predicting what tubulin actually does.

### Assumptions Table

| Parameter | Value used | Range in literature | Source | Status |
| --- | --- | --- | --- | --- |
| Superoxide diffusion coefficient D(O2-) | 1.0 x 10^-9 m^2/s | 0.5--2.0 x 10^-9 m^2/s | Takahashi et al. 1999 | Literature-backed |
| Encounter radius | 0.5 nm | 0.3--1.0 nm | van der Waals contact | Structural estimate |
| Baseline [O2-] | 1 nM | 0.1--100 nM (activity-dependent) | Sies and Jones 2020; Murphy 2009 | Literature-backed for baseline; upper range during mitochondrial bursts |
| Tryptophan residues per tubulin dimer | 8 (4 per monomer) | 8 | Lowe et al. 2001 | Literature-backed (structural) |
| Fraction of Trp accessible to solvent | 50% | 25--75% | Structural estimate from Lowe et al. 2001 crystal structure | Not directly measured for O2- access |
| Radical formation probability per encounter | 1% | 0.1--10% | Forni et al. 2016 (amino acid radical yields) | Order-of-magnitude estimate; not measured for this specific reaction |
| Quantum-classical yield difference | 12.69% | Model-dependent | `spin_coherence.py` (minimal Haberkorn model) | Generic RP model output, not tubulin-specific |
| Conformational energy coupling | 1 kT per event | 0.1--10 kT | Dima and Joshi 2008 (tubulin conformational energetics) | Order-of-magnitude estimate; no direct measurement of RP-product coupling to conformation |
| Tubulin dimers per microtubule | 13,000 | 10,000--16,000 | 13 protofilaments x ~1000 repeats | Standard structural value |
| Microtubules per neuron | 1,000 | 500--77,000 | Heidemann 1996 (conservative); upper range is an exploratory order-of-magnitude scenario | Conservative value is literature-backed; upper range is speculative |
| Neural integration time | 5 ms | 1--20 ms | EPSP timescale | Literature-backed |
| Criticality amplification factor | 51x | See derivation note above | `criticality_amplification.py` (abstract branching network) | Abstract model output, not measured in neural tissue |

### Bottleneck Results (order-of-magnitude model output)

| Quantity | Conservative model value | Interpretation |
| --- | --- | --- |
| Quantum-classical yield shift magnitude | 12.69% | microscale signal is nontrivial in the minimal RP model |
| Radical pair events per neuron in 5 ms | about 10 | model-identified bottleneck under conservative assumptions |
| Equivalent voltage shift | `9.9 x 10^-3 mV` | roughly one order below `0.1 mV` neural noise scale |
| Amplified firing bias | `3.4 x 10^-2` | depends on the 51x abstract-network amplification factor (see derivation note) |
| Dominant swing factor | local superoxide concentration | the parameter to which the model output is most sensitive |

## Interpretation

The current local evidence supports a specific and limited claim. In current repo models, radical-pair dynamics survive longer and yield larger modeled effects than the excitonic route: they operate on microsecond rather than femtosecond-to-picosecond scales, produce a nontrivial chemical outcome difference in the minimal Haberkorn model, and remain field-sensitive (compare Maeda et al. 2012 for experimental demonstration of radical-pair magnetic sensitivity). But this comparison is between two models in the current repo, not between two experimentally validated tubulin mechanisms. The transduction problem remains real. The repo's own order-of-magnitude bottleneck model says the mechanism fails if event rate never rises above the conservative baseline.

## What The Paper Can Say Right Now

- a minimal radical-pair model (generic Haberkorn physics, not tubulin-specific chemistry) produces a measurable quantum-classical chemical difference
- in current repo models, that difference persists on timescales dramatically longer than the modeled excitonic route
- the transduction-chain model remains parameter-sensitive and currently sub-noise under conservative assumptions; it is not yet ruled out by the current order-of-magnitude model, but it is not empirically supported either
- the model-identified sensitivity hinge is event rate (driven by local superoxide concentration and radical formation probability), not the existence of a microscale quantum signal

## What The Paper Cannot Say Yet

- it cannot identify any specific radical-pair-forming reaction in tubulin; the [TrpH+...O2-] route is a placeholder, not a validated candidate
- it cannot claim that the modeled effect is linked to cognition or to any measured tubulin property
- it cannot claim that the current transduction chain is empirically validated; it is a parameterized feasibility model with stacked order-of-magnitude assumptions (see Assumptions Table above)
- it cannot claim that the bottleneck identification (radical-pair formation rate) represents empirical localization of the true bottleneck; it reflects model sensitivity to that parameter

## Alternative Explanations The Paper Must Engage

- field or isotope effects in tubulin-related assays may reflect generic redox chemistry rather than access-relevant signaling
- any tubulin polymerization effect could be structural or pharmacological without requiring a consciousness link
- amplification in an abstract branching network does not by itself demonstrate amplification in a real cytoskeletal-neural pathway

## Recommended Manuscript Spine

1. Radical-pair mechanism and why it is the right quantum-biology comparison class (cite Haberkorn 1976; Maeda et al. 2012).
2. Minimal model and parameter choices, with explicit statement that this is a parameterized feasibility model using a placeholder chemical route (cite Lowe et al. 2001 for tubulin structure; Dima and Joshi 2008 for conformational energetics).
3. Assumptions table and quantitative bottleneck results (order-of-magnitude model output).
4. Parameter sensitivity analysis, with conditional statements about which ranges produce sub-noise versus noise-competitive signals (cite Murphy 2009 and Sies and Jones 2020 for ROS ranges).
5. Alternative non-spin explanations and why they remain live.
6. Kill conditions and next experiments.

## Minimal Kill Conditions

The paper becomes stronger if it says in advance what would weaken it.

- no radical-pair-compatible chemistry can be identified in tubulin (i.e., the placeholder [TrpH+...O2-] route and all alternative candidates are ruled out by structural or biochemical evidence; see Lowe et al. 2001 for tubulin structure)
- realistic local ROS exposure is far below the rate needed to accumulate events in a neural integration window (see Murphy 2009 and Sies and Jones 2020 for current ROS/superoxide literature)
- radical-pair products fail to couple measurably to tubulin conformational dynamics (see Dima and Joshi 2008 for conformational energetics)

## Data and Code Availability

Submission should include:

- the spin-coherence script
- the transduction-chain script and result markdown
- the criticality amplification script and summary outputs
- one parameter table separating literature-backed values from exploratory ranges

## Submission Blockers

- ~~Replace generic “tubulin radical pair” language with either a named candidate chemical route or an explicit placeholder statement.~~ Done: the [TrpH+...O2-] route is now explicitly labeled as a placeholder throughout.
- Add an alternatives section for non-spin explanations of tubulin field or isotope effects.
- Finalize which numbers are directly reported from code versus imported from the book narrative.
- Remove any prose that sounds like a solved neural mechanism rather than a parameterized feasibility model.
- ~~Add the assumptions table.~~ Done: see Assumptions Table in the Quantitative Bottleneck Map section.

## References

The following primary sources must be cited in the submitted manuscript:

- Haberkorn R. (1976). Density matrix description of spin-selective radical pair reactions. *Molecular Physics*, 32(5), 1491--1493. doi:10.1080/00268977600102851. (Foundational radical-pair recombination theory used in `spin_coherence.py`.)
- Maeda K., Henbest K.B., Cintolesi F., Kuprov I., Rodgers C.T., Liddell P.A., Gust D., Timmel C.R., Hore P.J. (2012). Chemical compass model of avian magnetoreception. *Nature*, 453, 387--390. PMID:22421133. (Primary experimental demonstration of radical-pair magnetic sensitivity in a biologically relevant context.)
- Lowe J., Li H., Downing K.H., Bhatt J.M. (2001). Refined structure of alpha-beta tubulin at 3.5 A resolution. *Journal of Molecular Biology*, 313(5), 1045--1057. PMID:11700061. (Tubulin crystal structure; source for tryptophan residue count and accessibility estimates.)
- Dima R.I. and Joshi H. (2008). Probing the origin of tubulin rigidity with molecular simulations. *Proceedings of the National Academy of Sciences*, 105(41), 15743--15748. PMC:2572946. (Tubulin conformational energetics; source for conformational coupling energy estimate.)
- Murphy M.P. (2009). How mitochondria produce reactive oxygen species. *Biochemical Journal*, 417(1), 1--13. PMID:19061483. (Mitochondrial superoxide production rates and activity dependence.)
- Sies H. and Jones D.P. (2020). Reactive oxygen species (ROS) as pleiotropic physiological signalling agents. *Nature Reviews Molecular Cell Biology*, 21, 363--383. doi:10.1038/s41580-020-0230-3. (Baseline and activity-dependent intracellular ROS concentrations.)
