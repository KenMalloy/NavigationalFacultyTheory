# How to Falsify Quantum Accounts of Conscious Access

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Methods and philosophy-of-science paper |
| Current status | Standalone draft; publishable if narrowed to conscious access and centered on an explicit framework table |
| Supports book material | `book_draft_v2.md` Chapter 15 |
| Best venue class | Consciousness methodology, philosophy of science, theory-driven methods |
| Core risk | It reads like a manifesto unless every claim about "what has been shown" is tied to a specific result file, script, or primary citation, and the paper functions as a concrete decision framework for researchers |

## Abstract

This manuscript should be positioned as a discriminative-testing framework for conscious-access hypotheses, using quantum-linked proposals as the case study rather than as the foregone conclusion. The paper proposes three evidential levels as a working framework: substrate evidence that a quantum effect exists in a biological medium, linkage evidence that perturbing that effect changes conscious access, and discriminative evidence that the resulting pattern is not equally predicted by classical alternatives. The repo already contains useful negative-result case studies: the ENAQT failure path ([phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py)), the propofol topology-first failure ([temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv); [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py)), and the benchmark reframing away from broad proof language ([by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md)). That honesty should be turned into the paper’s organizing virtue.

## Three Evidential Levels

The paper proposes these three levels as a working framework for organizing evidential claims in the quantum-consciousness literature. They do not represent a consensus standard in the field; the contribution is to make them explicit and actionable. The paper becomes much more publishable if it treats these levels as the entire methodological core rather than as one paragraph among many.

| Level | Question | What counts as success | What does not count |
| --- | --- | --- | --- |
| Substrate | Does the proposed quantum effect exist in the medium? | direct spin, transport, field, isotope, or coherence evidence in the relevant biological substrate | behavioral anomalies with no substrate readout |
| Linkage | Does perturbing the effect change conscious access? | within-state perturbation coupled to access-sensitive outcome measures | across-state differences confounded by arousal or pharmacology |
| Discriminative | Is the perturbation pattern better predicted by the quantum-linkage model than by classical alternatives? | preregistered model comparison with explicit classical rivals | generic complexity changes, post hoc storytelling, or single positive anomalies |

## Core Framework

The single most important addition is one explicit framework table. The kill conditions listed here are methodological recommendations intended to make each hypothesis testable. They remain conceptual until an experiment is run against them; the value is in stating them in advance.

| Hypothesis | Required substrate | Linkage prediction | Classical alternative | Within-state assay | Kill condition |
| --- | --- | --- | --- | --- | --- |
| Excitonic ENAQT drives access-relevant transport | robust tubulin-scale ENAQT under physiological noise | transport-linked marker changes with ENAQT-relevant perturbation | classical stochastic transport or no meaningful transport effect | ex vivo transport assay plus matched thermal controls | no robust ENAQT window under physiological constraints |
| Radical-pair chemistry modulates conscious access | tubulin-compatible radical-pair chemistry and measurable downstream coupling | field or isotope sensitivity tracks access within matched arousal states | field or isotope effects reflect generic chemistry, stress, or arousal shifts | within-state conscious report paradigm with sham, field, and chemistry controls | substrate perturbation changes no access-relevant measure beyond classical confounds |
| Qualitative character depends on structured back-action | measurement-like biological update with intrinsic disturbance | changing disturbance statistics alters reportable quality while gross function is held approximately fixed | report changes follow ordinary sensory or energetic perturbation only | disturbance-statistics manipulation in a tightly controlled surrogate or biological system | no disturbance-specific effect once classical confounds are matched |
| Topology-first anesthesia signature | topology adds causal lead over classical EEG markers | TDA metrics change before classical metrics | topology follows or covaries with standard EEG changes | acquisition-ordered or induction-timed anesthesia analysis | topology does not lead classical comparators |

## Worked Exemplar

The paper should include one complete worked example rather than many partial ideas.

### Within-state conscious-access dissociation

Within-state paradigms that hold arousal and task demands fixed while varying access-relevant perturbations are essential for discriminative testing. For adversarial-collaboration approaches to structuring such comparisons, see the COGITATE protocol ([Melloni et al. 2023](https://pubmed.ncbi.nlm.nih.gov/36763595/)) and its primary results paper ([Cogitate Consortium et al. 2024](https://doi.org/10.1038/s41562-024-02106-4)). For a recent critical discussion of within-state paradigm design in the consciousness literature, see [Naccache et al. 2025](https://doi.org/10.1093/nc/niae046).

Use a paradigm where task demands, behavioral performance floor, and arousal are tightly controlled, then test whether a substrate-targeted perturbation shifts:

- reportability
- confidence
- access-sensitive neural markers

without producing the same pattern expected from a generic arousal or sensory confound.

The point of the exemplar is procedural. A reviewer should be able to see what counts as:

- a substrate manipulation
- a linkage prediction
- a classical confound
- a negative result

### Suggested worked design

| Element | Concrete version |
| --- | --- |
| Target construct | conscious access, not consciousness in general |
| Task | masked visual discrimination with confidence report and low-report control blocks |
| Perturbation | weak-field or chemistry-linked substrate perturbation paired with sham |
| Primary outcomes | reportability, confidence, and an access-sensitive neural marker |
| Classical confounds to model explicitly | arousal drift, criterion shift, sensory noise, response bias |
| Negative outcome | no perturbation effect beyond those confounds, or equal explanatory power for a purely classical model |

The important feature is not the exact task. It is the decision rule. A publishable methods paper needs to tell the reader what result would make the hypothesis weaker.

## Why This Paper Is Stronger As A Methods Paper

- It can use NFT as the motivating case without requiring NFT to be accepted.
- It gains credibility from the repo’s existing negative-result case studies, each tied to a specific script or output file.
- It becomes useful to skeptics as well as proponents.

## Already Falsified, Weakened, And Still Open

This section is one of the best ways to make the paper feel serious rather than promotional.

| Status | Claim family | Current local state | Source |
| --- | --- | --- | --- |
| Weakened | topology-first propofol prediction | current acquisition-ordered reanalysis does not support it; note that this is an acquisition-ordered proxy result, not a direct induction-timed analysis, so the weakening is suggestive rather than definitive | [temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv); [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py) |
| Weakened | excitonic ENAQT route | in the current geometry-informed physiological baseline, transport efficiency does not show an intermediate-noise ENAQT peak; other tubulin-derived geometries or model classes are not ruled out | [phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py) |
| Still open | radical-pair substrate relevance to access | substrate-level feasibility modeling exists ([spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py)), but feasibility is not linkage; no experiment yet connects radical-pair perturbation to any conscious-access measure | [spin_coherence.py](/Users/kennethmalloy/nft/enaqt_simulation/spin_coherence.py) |
| Still open | structured back-action account | conceptually sharp, empirically distant; this remains in the "still open" ledger, not the "supported" ledger, because no surrogate or limiting-case test has been run | [07_qualia_back_action.md](/Users/kennethmalloy/nft/paper/manuscripts/07_qualia_back_action.md) |

That ledger changes the paper's tone for the better. It shows that the framework is willing to lose.

## Relationship To The Companion Conceptual Paper

This manuscript should explicitly name `07_qualia_back_action.md` as a companion.

- the companion conceptual paper defines the ontological commitments
- this paper defines how those commitments could fail

That pairing makes both manuscripts stronger and keeps this one from drifting into metaphysics.

## What Is Already Evidenced In This Repo

- the ENAQT path already has a failure narrative and dedicated code scaffolding: in the current geometry-informed physiological baseline, transport does not show an ENAQT peak ([phase2_transport.py](/Users/kennethmalloy/nft/enaqt_simulation/phase2_transport.py))
- the propofol topological prediction is already locally weakened by an acquisition-ordered proxy reanalysis (not a direct induction-timed analysis): topology did not precede classical comparators in this dataset ([temporal_ordering_stats.csv](/Users/kennethmalloy/nft/results/temporal_ordering_stats.csv); [04_temporal_ordering.py](/Users/kennethmalloy/nft/nft-tda-reanalysis/04_temporal_ordering.py))
- the navigation benchmark has already been reframed away from inflated proof language; only the 3D/6D family shows a confidence interval excluding zero ([by_dimension.md](/Users/kennethmalloy/nft/enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md))

## Relationship To Pre-Registration

The paper should recommend a COGITATE-style discipline ([Melloni et al. 2023 protocol](https://pubmed.ncbi.nlm.nih.gov/36763595/); [Cogitate Consortium et al. 2024 results](https://doi.org/10.1038/s41562-024-02106-4)) for every future experiment:

- state the competing models in advance
- lock the primary endpoint
- lock the confounds that will be modeled
- define a negative outcome before data are collected

That is what turns a controversial topic into cumulative science.

## Submission Blockers

- Replace generic “predictions matrix” prose with the explicit table above or a stronger version of it.
- Expand the worked exemplar into full manuscript prose with design, confounds, analysis plan, and kill condition.
- Keep the target construct to conscious access throughout the manuscript.
- Finalize citations and remove any remaining portfolio-era planning language.
