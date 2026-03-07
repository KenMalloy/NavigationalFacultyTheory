# Manuscript Evidence Audit

Audit date: 2026-03-16

Support-type legend:

- `Local repo output`: directly supported by code, result files, or reproducible local outputs in this workspace.
- `Primary literature`: directly supported by primary papers or datasets.
- `Interpretive synthesis`: a conceptual integration or inference that is not directly tested as stated.
- `Speculative / forward-looking`: conjectural, ontological, or dependent on unvalidated assumptions.

Verification note:

- Fresh reruns in this workspace: [branching_navigation_sim.py](/Users/kennethmalloy/nft/simulations/branching_navigation_sim.py), [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py), [spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py), [criticality_amplification.py](/Users/kennethmalloy/nft/enaqt_simulation/criticality_amplification.py).
- Read from existing local outputs, not freshly rerun here: [by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md), [by_dimension_bin.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension_bin.md), [transduction_chain_results.md](/Users/kennethmalloy/nft/enaqt_simulation/transduction_chain_results.md), [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv).
- Fresh rerun attempt failed for [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py) because the current repo Python environment lacks `pandas`; the propofol manuscript therefore rests on existing output files plus code inspection, not a fresh execution in this audit.

## 01_trajectory_entropy_unification.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| Conscious access can be organized as a navigation problem that reduces uncertainty over future trajectories under action and resource constraints. | Interpretive synthesis | [Friston et al. 2017](https://pubmed.ncbi.nlm.nih.gov/27870614/), [Mashour et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/), [Albantakis et al. 2023](https://doi.org/10.1371/journal.pcbi.1011465) | Low-Medium | Present as the paper's proposal, not as an established empirical result. |
| Active inference, IIT, and GNWT can be decomposed into selection, integration, and propagation constraints on one shared control problem. | Interpretive synthesis | [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md), [Friston et al. 2017](https://pubmed.ncbi.nlm.nih.gov/27870614/), [Mashour et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/) | Low | Label the mapping as a heuristic correspondence table; do not imply consensus unification. |
| Trajectory entropy is a meaningfully different quantity from signal entropy in the consciousness literature. | Interpretive synthesis | [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md), [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532), [Casali et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23946194/) | Medium | Add a formal definition plus direct citations to the signal-complexity literature; avoid implying `trajectory entropy` is already a standard field term. |
| Different consciousness frameworks describe different constraints on the same trajectory-shaping process. | Interpretive synthesis | [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md) | Low | Recast as "this paper reads these frameworks as..." rather than "these frameworks are...". |
| Access to counterfactual branch structure improves performance in a branching environment. | Local repo output | [branching_navigation_sim.py](/Users/kennethmalloy/nft/simulations/branching_navigation_sim.py) | High | Keep the claim narrow and explicitly toy-model. |
| In the verified toy run, mean reward improves from `86.985` to `91.663` with budgeted branch access and to `98.437` with full branch awareness. | Local repo output | [branching_navigation_sim.py](/Users/kennethmalloy/nft/simulations/branching_navigation_sim.py) | High | None beyond adding the exact command and seed in the manuscript. |
| The toy result supports a weak functional claim about branch access, but not a mechanistic claim about consciousness. | Interpretive synthesis | [branching_navigation_sim.py](/Users/kennethmalloy/nft/simulations/branching_navigation_sim.py), [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md) | Medium | State this asymmetry explicitly in the abstract and discussion. |
| The repo already contains enough for a theory-plus-toy-model paper, but not direct brain-level evidence for trajectory entropy. | Local repo output | [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md), [branching_navigation_sim.py](/Users/kennethmalloy/nft/simulations/branching_navigation_sim.py) | High | Remove any `Results` wording that sounds like neural evidence until a direct trajectory-entropy analysis exists. |
| COGITATE and purported IIT/GNWT cortical proximity motivate an architectural rather than winner-take-all interpretation. | Interpretive synthesis | [book_draft_v1.md](/Users/kennethmalloy/nft/paper/book_draft_v1.md), [Melloni et al. 2023 protocol](https://pubmed.ncbi.nlm.nih.gov/36763595/) | Low | Either add the actual primary results/anatomy citations or cut this motivation from the paper. |

## 02_enaqt_negative_result.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| ENAQT should be tested in the same dephasing regime living cells actually occupy, not only in a coherence-favoring regime. | Interpretive synthesis | [Mohseni et al. 2008](https://pubmed.ncbi.nlm.nih.gov/19045332/), [Panitchayangkoon et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2919932/) | Medium | Frame this as the paper's discriminative test logic, not as a result. |
| In the default geometry-informed eight-site helix model, transport efficiency does not show an intermediate-noise ENAQT peak. | Local repo output | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | High | Keep "default geometry-informed helix model" in the claim every time. |
| In that baseline, the physiological regime is strongly dephasing-dominated (`kappa_phys / V = 40.5294`; `gamma/kappa = 0.0247`). | Local repo output | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | High | None beyond reporting the exact derivation and units. |
| Maximum transport efficiency occurs at the coherent limit (`gamma/kappa = 1000`, efficiency `0.3841`), while the physiological regime is lower (`~0.327`). | Local repo output | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | High | Report the full sweep figure and raw CSV, not only the headline values. |
| In the verified local baseline model, dephasing does not enhance transport. | Local repo output | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | High | Qualify with "baseline model"; do not generalize to tubulin writ large. |
| This negative result narrows the mechanism search but does not eliminate all tubulin-derived geometries or model classes. | Interpretive synthesis | [02_enaqt_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/02_enaqt_negative_result.md), [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | Medium | Add an explicit limitations paragraph immediately after the headline result. |
| The current manuscript does not yet support tubulin-specific generality. | Local repo output | [02_enaqt_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/02_enaqt_negative_result.md) | High | Retitle and re-abstract the paper around a geometry-informed baseline unless the structural ensemble is added. |
| The failure is informative because it falsifies one candidate transport route under a concrete physiological-style baseline. | Interpretive synthesis | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py), [Mohseni et al. 2008](https://pubmed.ncbi.nlm.nih.gov/19045332/) | Medium | Use "rules out this modeled route under these assumptions" rather than "rules out excitonic transport" in general. |

## 03_quantum_navigation_benchmark.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| The benchmark compares a learned quantum-adaptive controller with a matched learned classical-adaptive controller under fixed training budgets. | Local repo output | [maze_scaling_analysis_workflow.md](/Users/kennethmalloy/nft/enaqt_simulation/maze_scaling_analysis_workflow.md), [2026-03-15 benchmark summary](/Users/kennethmalloy/nft/docs/plans/2026-03-15-quantum-navigation-benchmark-summary.md) | High | Quote the fairness rules directly in the manuscript methods. |
| Across 90 confirmatory mazes, only the 3D/6D family shows a confidence interval excluding zero (`5.7700`, `[2.1145, 9.4255]`). | Local repo output | [by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md) | High | Keep this as the primary headline; everything else should be secondary or exploratory. |
| The 2D/5D and 4D/7D families are weak or inconclusive. | Local repo output | [by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md) | High | Do not imply monotonic scaling or universal advantage. |
| The observed signal is family-dependent and modest rather than universal. | Interpretive synthesis | [by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md) | Medium | Phrase as "in the current benchmark families". |
| The shortest-path planner remains the classical upper bound and solves every benchmark family considered. | Local repo output | [2026-03-15 benchmark summary](/Users/kennethmalloy/nft/docs/plans/2026-03-15-quantum-navigation-benchmark-summary.md) | Medium-High | Add per-maze planner results to the appendix so the claim is not resting on a prose summary alone. |
| Maze, not trial, is the unit of confirmatory inference. | Local repo output | [maze_scaling_analysis_workflow.md](/Users/kennethmalloy/nft/enaqt_simulation/maze_scaling_analysis_workflow.md) | High | None. This is already a strong methodological choice. |
| Harder 3D families and middle latent gaps look more promising than trivial mazes or maximal dimensionality. | Interpretive synthesis | [by_dimension_bin.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension_bin.md), [2026-03-15 benchmark summary](/Users/kennethmalloy/nft/docs/plans/2026-03-15-quantum-navigation-benchmark-summary.md) | Medium | Mark clearly as exploratory unless the family was fixed before inspection. |
| The paper does not show superiority over classical planning in general or any biological relevance. | Interpretive synthesis | [03_quantum_navigation_benchmark.md](/Users/kennethmalloy/nft/paper/manuscripts/03_quantum_navigation_benchmark.md) | High | Keep this non-claim explicit in the abstract and discussion. |

## 04_radical_pair_tubulin_feasibility.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| In the current Haberkorn-style minimal model, Earth-field radical-pair dynamics show a `1.480 us` coherence lifetime, `12.69%` singlet-yield shift, and `10 us` quantum-classical divergence window. | Local repo output | [spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py), [Haberkorn 1976](https://doi.org/10.1080/00268977600102851) | High | Report this explicitly as a minimal radical-pair model, not tubulin-specific chemistry. |
| The same repo shows stronger near-critical amplification than subcritical amplification (`10.24%` at `sigma=1.00` vs `3.63%` at `sigma=0.90`; ratio `2.8x`). | Local repo output | [criticality_amplification.py](/Users/kennethmalloy/nft/enaqt_simulation/criticality_amplification.py) | High | Keep the claim qualitative; avoid turning this into a validated neural transduction factor. |
| The conservative transduction-chain calculation gives roughly `10` RP events per neuron per `5 ms`, an equivalent voltage of `9.9 x 10^-3 mV`, and a signal about one order below a `0.1 mV` noise scale. | Local repo output | [transduction_chain_results.md](/Users/kennethmalloy/nft/enaqt_simulation/transduction_chain_results.md) | Medium | Present as order-of-magnitude model output only; add a visible assumptions table. |
| Event rate and local superoxide concentration are the dominant bottlenecks in the current transduction model. | Local repo output | [transduction_chain_results.md](/Users/kennethmalloy/nft/enaqt_simulation/transduction_chain_results.md), [Murphy 2009](https://pubmed.ncbi.nlm.nih.gov/19061483/), [Sies and Jones 2020](https://www.nature.com/articles/s41580-020-0230-3) | Medium | State that this is model sensitivity, not empirical localization of the true bottleneck. |
| Radical-pair dynamics are a better mechanistic candidate than the discarded excitonic route because the modeled timescales are longer and the chemical effect is larger. | Interpretive synthesis | [spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py), [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py), [Maeda et al. 2012](https://pubmed.ncbi.nlm.nih.gov/22421133/) | Medium | Say "in current repo models" and avoid implying tubulin relevance has been shown. |
| The transduction chain is thin but not obviously dead, and favorable assumptions could close the gap. | Speculative / forward-looking | [transduction_chain_results.md](/Users/kennethmalloy/nft/enaqt_simulation/transduction_chain_results.md) | Low | Replace with a conditional statement tied to specific parameter ranges; do not use viability rhetoric without data. |
| The manuscript currently lacks biochemical specificity for any actual tubulin radical pair. | Local repo output | [04_radical_pair_tubulin_feasibility.md](/Users/kennethmalloy/nft/paper/manuscripts/04_radical_pair_tubulin_feasibility.md), [Lowe et al. 2001](https://pubmed.ncbi.nlm.nih.gov/11700061/) | High | Replace generic "tubulin radical pair" language with an explicit placeholder or named candidate route. |
| The current transduction chain is not empirically validated; it is a stacked assumption model. | Interpretive synthesis | [transduction_chain_results.md](/Users/kennethmalloy/nft/enaqt_simulation/transduction_chain_results.md) | High | Use "parameterized feasibility model" instead of mechanism-confirming language. |

## 05_discriminative_program.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| Quantum-linked accounts of conscious access should be evaluated at three evidential levels: substrate, linkage, and discriminative evidence. | Interpretive synthesis | [05_discriminative_program.md](/Users/kennethmalloy/nft/paper/manuscripts/05_discriminative_program.md), [Melloni et al. 2023 protocol](https://pubmed.ncbi.nlm.nih.gov/36763595/) | Medium-High | Present as a proposed framework, not as a field standard that already exists. |
| Explicit kill conditions are essential to keep controversial consciousness claims cumulative rather than rhetorical. | Interpretive synthesis | [05_discriminative_program.md](/Users/kennethmalloy/nft/paper/manuscripts/05_discriminative_program.md) | High | None; this is a sound methodological recommendation, but still conceptual. |
| The repo already demonstrates negative-result discipline through the ENAQT failure path, the propofol topology-first failure, and the benchmark reframing. | Local repo output | [02_enaqt_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/02_enaqt_negative_result.md), [03_quantum_navigation_benchmark.md](/Users/kennethmalloy/nft/paper/manuscripts/03_quantum_navigation_benchmark.md), [06_propofol_tda_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/06_propofol_tda_negative_result.md) | High | Keep this as a strength, but link each case to the exact result file or script. |
| The excitonic ENAQT route is already weakened. | Local repo output | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) | High | Qualify with "in the current geometry-informed physiological baseline". |
| The topology-first propofol prediction is already weakened. | Local repo output | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv) | Medium-High | Note that the support is an acquisition-ordered proxy result, not a direct induction-timed analysis. |
| Radical-pair substrate relevance to conscious access remains open. | Interpretive synthesis | [spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py), [Maeda et al. 2012](https://pubmed.ncbi.nlm.nih.gov/22421133/) | Low-Medium | Keep as explicitly open; do not let "feasibility" drift into "linkage". |
| The structured back-action account remains conceptually sharp but empirically distant. | Interpretive synthesis | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Medium | Keep it in the "still open" ledger, not the "supported" ledger. |
| Within-state, access-targeted perturbation designs are needed; across-state comparisons are too confounded by arousal and pharmacology to do the whole job. | Interpretive synthesis | [Melloni et al. 2023 protocol](https://pubmed.ncbi.nlm.nih.gov/36763595/), [Naccache et al. 2025](https://doi.org/10.1093/nc/niae046) | Medium | Add direct primary citations for representative within-state paradigms rather than leaving this as generic methods prose. |

## 06_propofol_tda_negative_result.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| The local pipeline computes both classical EEG features and persistent-homology-derived metrics on OpenNeuro `ds005620`. | Local repo output | [nft-tda-reanalysis README](/Users/kennethmalloy/nft/nft-tda-reanalysis/README.md), [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0) | High | Cite the dataset DOI directly in the manuscript methods. |
| The current summary output does not support the topology-first prediction against either Lempel-Ziv complexity or alpha-band wPLI. | Local repo output | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv) | High | None, but make clear that this is the current output file, not a hand-transcribed result. |
| Median lead-lag differences are negative (`-57.0` epochs vs LZC; `-59.5` vs alpha wPLI). | Local repo output | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv) | High | Keep exact comparator names and numbers in the main table. |
| Topology-first proportions are low (`0.1176`, `0.1111`) and `nft_supported` is `False` for both primary comparators. | Local repo output | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv) | High | None. |
| The claim being weakened is an ordering claim, not the general usefulness of TDA in EEG. | Interpretive synthesis | [06_propofol_tda_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/06_propofol_tda_negative_result.md) | Medium | Preserve this distinction in the title, abstract, and conclusion. |
| The analysis is an acquisition-ordered proxy because `ds005620` does not expose true induction timing inside the rest recordings. | Local repo output | [nft-tda-reanalysis README](/Users/kennethmalloy/nft/nft-tda-reanalysis/README.md), [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py) | High | Put this limitation in the abstract, not only the methods. |
| Current support comes from existing local outputs rather than a fresh rerun in this workspace. | Local repo output | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv), [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py) | High | Re-run in a pinned environment before submission and archive the exact environment file. |
| The paper weakens a specific directional prediction in a public dataset and is therefore publishable as a negative-result methods paper if the proxy limitation is front-and-center. | Interpretive synthesis | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv), [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0) | Medium | Do not oversell to "topology is not useful" or "topology never precedes". |

## 07_qualia_back_action.md

| Claim | Current support type | Strongest source | Confidence | Revision needed |
| --- | --- | --- | --- | --- |
| Subjective character may have a specific physical address in measurement-like update processes with intrinsic disturbance. | Speculative / forward-looking | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md), [Hatridge et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23307736/), [Cripe et al. 2019](https://www.nature.com/articles/s41586-019-1051-4) | Low | State plainly that this is a conjectural constraints proposal, not an evidenced biological mechanism. |
| Disturbance-bearing implementation differences could matter phenomenally, not just functionally. | Speculative / forward-looking | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Low | Mark as an ontological commitment rather than a supported finding. |
| A measurement-like biological update should require information gain, irreducible disturbance, and downstream control consequences tied to disturbance statistics. | Interpretive synthesis | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Medium | Label as a stipulative working definition. |
| The proposal is not equivalent to ordinary Bayesian updating because physical disturbance matters. | Interpretive synthesis | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Medium | Keep as a conceptual contrast, not an empirical dissociation claim. |
| A back-action-evasion analogue would be philosophically and scientifically decisive. | Speculative / forward-looking | [Moller et al. 2017](https://www.nature.com/articles/nature22980), [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Low | Describe as a long-range thought-experimental discriminator, not an imminent experiment. |
| Matched-input systems with different disturbance statistics need not be phenomenally equivalent. | Speculative / forward-looking | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Low | Keep hypothetical and avoid language that presumes phenomenal facts about artificial systems. |
| Attention may operate as disturbance shaping and thereby modulate phenomenal intensity. | Speculative / forward-looking | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | Low | Recast as a possible case study, not a mechanistic claim. |
| The paper does not solve the hard problem or stand as an empirical paper on its own. | Interpretive synthesis | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | High | Keep this non-claim near the front of the manuscript. |

## Bibliography Cleanup

### Missing citations

- `01`: add direct primary citations for active inference, GNWT, and IIT rather than relying on broad theory labels. Recommended anchors: [Friston et al. 2017](https://pubmed.ncbi.nlm.nih.gov/27870614/), [Mashour et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/), [Albantakis et al. 2023](https://doi.org/10.1371/journal.pcbi.1011465).
- `01` and `05`: add the actual COGITATE primary results paper. Right now the repo materials more clearly expose the protocol and reaction pieces than the final Nature results citation. At minimum cite the protocol directly: [Melloni et al. 2023 protocol](https://pubmed.ncbi.nlm.nih.gov/36763595/).
- `01`: if the manuscript contrasts `signal entropy` with `trajectory entropy`, add primary complexity/state-literature anchors such as [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532) and [Casali et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23946194/).
- `02`: add primary ENAQT theory/experiment anchors rather than generic quantum-biology summaries: [Mohseni et al. 2008](https://pubmed.ncbi.nlm.nih.gov/19045332/), [Panitchayangkoon et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2919932/).
- `04`: add primary radical-pair chemistry anchors: [Haberkorn 1976](https://doi.org/10.1080/00268977600102851), [Maeda et al. 2012](https://pubmed.ncbi.nlm.nih.gov/22421133/).
- `04`: add direct structural/biophysical citations for tubulin geometry and conformational energetics: [Lowe et al. 2001](https://pubmed.ncbi.nlm.nih.gov/11700061/), [Dima and Joshi 2008](https://pmc.ncbi.nlm.nih.gov/articles/PMC2572946/).
- `06`: add the dataset DOI and primary comparator methods: [OpenNeuro ds005620](https://doi.org/10.18112/openneuro.ds005620.v1.0.0), [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532), [Vinck et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21276857/), [Reimann et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467434/).
- `07`: if the paper invokes measurement back-action and back-action evasion, cite the relevant physics directly: [Hatridge et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23307736/), [Cripe et al. 2019](https://www.nature.com/articles/s41586-019-1051-4), [Moller et al. 2017](https://www.nature.com/articles/nature22980).

### Weak citations or weak citation habits

- All seven manuscripts currently lean too heavily on local repo prose, book-draft narrative, or internal planning files as argumentative support. Those are useful for drafting but not citable evidence.
- `01`: any appeal to "COGITATE plus cortical proximity implies architectural unification" is weak until it is tied to direct neuroanatomy papers and the actual COGITATE results paper.
- `03`: the statement that shortest-path planning is the classical upper bound is credible locally, but it currently rests on internal benchmark summaries. The published paper should cite the exact benchmark definition and append the planner outputs, not only a narrative memo.
- `04`: the transduction-chain writeup uses a `51x` amplification factor derived from `10.2 / 0.2`; the currently rerun [criticality_amplification.py](/Users/kennethmalloy/nft/enaqt_simulation/criticality_amplification.py) more directly supports a `10.24%` effect at `epsilon = 0.002` and a `2.8x` critical-vs-subcritical comparison. The manuscript should explain this derivation or soften the claim.
- `04`: the claim of "one billion tubulin dimers per cortical neuron" is currently too loose. It needs a traceable primary source or should be rewritten as an exploratory order-of-magnitude scenario.
- `06`: TDA-specific motivation should not rest only on repo README text. Cite a direct neural-topology paper such as [Reimann et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467434/) and then state clearly that scalp-EEG persistent homology is only a coarse proxy.
- `07`: avoid relying on QBism-adjacent or broad philosophy-of-mind commentary as if it were evidence for a biological back-action mechanism.

### Claims that need primary sources instead of secondary summaries

- Any mention of COGITATE participant count, modality count, or which theory "won" needs the actual primary results paper, not institutional news or commentary.
- Any claim that ENAQT peaks at intermediate dephasing in biological systems should be tied to primary ENAQT theory/experiment papers, not only review summaries.
- Any claim that radical pairs are magnetically sensitive in biologically relevant media should be tied to direct spin-chemistry or cryptochrome experiments such as [Maeda et al. 2012](https://pubmed.ncbi.nlm.nih.gov/22421133/).
- Any statement that room-temperature quantum back-action has been observed should cite [Cripe et al. 2019](https://www.nature.com/articles/s41586-019-1051-4) directly.
- Any claim about propofol-era complexity measures or wPLI should cite the primary methods/results papers, not only repo outputs: [Schartner et al. 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532), [Vinck et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21276857/).
- Any claim about tubulin residue counts, geometry, or conformational energetics should cite direct structural/biophysical sources such as [Lowe et al. 2001](https://pubmed.ncbi.nlm.nih.gov/11700061/) and [Dima and Joshi 2008](https://pmc.ncbi.nlm.nih.gov/articles/PMC2572946/).

## Red-Flag Phrases

These phrases overclaim relative to the current evidence base, or need tighter qualifiers.

- `conscious access can be organized as a navigation problem` -> safer: `this paper proposes a navigation-based organizing framework for conscious access`
- `trajectory entropy is the common bookkeeping variable` -> safer: `trajectory entropy is introduced here as a candidate bookkeeping variable`
- `COGITATE ... motivates an architectural rather than winner-take-all interpretation` -> safer: `COGITATE is consistent with, but does not by itself establish, an architectural reading`
- `the physiological regime is deeply dephasing-dominated` -> safer: `in the default helix baseline, the modeled physiological regime is strongly dephasing-dominated`
- `dephasing does not enhance transport` -> safer: `dephasing does not enhance transport in the verified baseline model`
- `the clearest current positive result` -> safer: `the strongest current local benchmark signal`
- `harder maze families and medium latent gaps are more promising` -> safer: `in the current benchmark families, harder 3D cases and middle latent gaps look more promising`
- `radical-pair dynamics are a far better mechanistic candidate` -> safer: `in current repo models, radical-pair dynamics survive longer and yield larger modeled effects than the excitonic route`
- `the transduction chain is thin but not obviously dead` -> safer: `the transduction-chain model remains parameter-sensitive and currently sub-noise under conservative assumptions`
- `conditionally viable` -> safer: `not yet ruled out by the current order-of-magnitude model`
- `already contains a serious advantage` -> safer: `already contains useful negative-result case studies`
- `topological features do not precede classical EEG markers` -> safer in body text: `did not precede them in this acquisition-ordered proxy reanalysis`
- `provide a candidate physical locus for qualitative character` -> safer: `offer a conjectural candidate physical locus`
- `back-action cannot be epiphenomenal` -> safer: `the proposal commits to disturbance having a non-epiphenomenal role`
- `matched-input systems ... need not be phenomenally equivalent` -> safer: `the proposal predicts a possible phenomenal difference despite matched inputs and outputs`

## Safe-to-Submit-After-Edits Ranking

| Rank | Manuscript | Why this rank |
| --- | --- | --- |
| 1 | [03_quantum_navigation_benchmark.md](/Users/kennethmalloy/nft/paper/manuscripts/03_quantum_navigation_benchmark.md) | Strongest directly evidenced local result set, a clear confirmatory workflow, and the least dependence on unresolved metaphysics. The main risk is claim inflation beyond the matched-baseline benchmark. |
| 2 | [06_propofol_tda_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/06_propofol_tda_negative_result.md) | Narrow, falsifiable, and grounded in a public dataset plus an existing pipeline. The main limitation is that the ordering analysis is only an acquisition-ordered proxy and was not freshly rerun in this audit environment. |
| 3 | [02_enaqt_negative_result.md](/Users/kennethmalloy/nft/paper/manuscripts/02_enaqt_negative_result.md) | Clean local negative result with a defensible narrow headline. It drops quickly in safety if it continues to imply tubulin-specific generality. |
| 4 | [04_radical_pair_tubulin_feasibility.md](/Users/kennethmalloy/nft/paper/manuscripts/04_radical_pair_tubulin_feasibility.md) | Quantitatively richer than most of the conceptual papers, but chemistry identity, parameter realism, and transduction assumptions are still major liabilities. |
| 5 | [05_discriminative_program.md](/Users/kennethmalloy/nft/paper/manuscripts/05_discriminative_program.md) | Methodologically useful and honest, but mostly conceptual. It can be publishable if it becomes a concrete decision framework rather than manifesto prose. |
| 6 | [01_trajectory_entropy_unification.md](/Users/kennethmalloy/nft/paper/manuscripts/01_trajectory_entropy_unification.md) | Interesting synthesis plus one solid toy result, but the main consciousness-level claims still outrun what is evidenced. It needs more disciplined scoping than it currently has. |
| 7 | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) | The sharpest conceptual risk and the weakest empirical anchor. It is potentially valuable as a constraints essay, but not yet safe if framed as anything stronger than a conjectural companion paper. |
