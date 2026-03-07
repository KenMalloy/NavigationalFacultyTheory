# Conscious Processing as Trajectory-Entropy Reduction

## Title

Conscious Processing as Trajectory-Entropy Reduction: A Navigational Synthesis of Active Inference, Integrated Information, and Global Workspace

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Theory and synthesis paper with a verified toy example |
| Current status | Much closer to publishable as a theory-plus-toy-model paper |
| Supports book material | Chapters 1, 3, and 4 |
| Best venue class | Consciousness theory, formal cognitive science, philosophy of cognitive science |
| Core risk | The paper overreaches if it implies new empirical confirmation rather than a new organizing frame |

## Abstract

This manuscript is a theory paper with one modest computational supplement. It proposes a navigation-based organizing framework for conscious access, in which a system reduces uncertainty over future trajectories under action and resource constraints. The paper does not replace active inference (Friston et al. 2017), Integrated Information Theory (Albantakis et al. 2023), or Global Neuronal Workspace Theory (Mashour et al. 2020). It instead offers a heuristic correspondence table that reads active inference as constraining selection, IIT as constraining integration, and GNWT as constraining propagation, while treating generation as the upstream source of candidate trajectories. A locally verified toy branching simulation shows that access to counterfactual branch structure improves performance in a simple decision environment, supporting a narrow functional claim: branch access helps in branching environments. The stronger mechanistic claim -- that biological conscious access actually operates this way -- is not supported by this toy model and remains explicitly open.

## Introduction

The cleanest motivation for this paper is the field's pattern of partial success. Existing consciousness theories often explain different parts of the phenomenon well while failing to close the whole gap. Recent adversarial-collaboration efforts such as the COGITATE protocol (Melloni et al. 2023) are consistent with, but do not by themselves establish, an architectural reading in which multiple theories describe complementary constraints rather than competing for a single winner-take-all explanation. This manuscript takes that possibility as its starting point but keeps its scope narrow: it is about conscious access, task-level control, and theory decomposition, not about solving the hard problem.

The paper's real claim is architectural. It proposes that a family of successful theories can be read as describing distinct constraints on the same control problem: how a bounded system shapes the distribution of its own future trajectories. This paper reads these frameworks as complementary constraint families, not as already-unified components of a single established model.

## Contribution

The publishable version of this paper has four concrete jobs.

1. State that it is a theory-and-synthesis paper rather than a hidden empirical paper.
2. Define trajectory entropy as a new organizing quantity, distinct from the signal-entropy and perturbational-complexity measures already established in the consciousness literature (Schartner et al. 2015; Casali et al. 2013), and make clear what is new and what is only a relabeling.
3. Show exactly where the mapping to IIT (Albantakis et al. 2023) and GNWT (Mashour et al. 2020) is a heuristic correspondence rather than a total derivation.
4. Use one verified toy model to show that counterfactual branch access is a coherent functional construct rather than metaphorical rhetoric.

## Core Formalism

**Definition.** Let a policy-conditioned trajectory over horizon `H` be `tau = (s_t:t+H, a_t:t+H)`. The paper’s organizing quantity, which we call *trajectory entropy*, is:

`H_tau(pi) = -E_p(tau | pi, M)[log p(tau | pi, M)]`

where `M` is the internal model used to assign probabilities over future trajectories.

*Trajectory entropy* is introduced here as a candidate bookkeeping variable; it is not yet a standard field term. It should not be confused with signal-entropy or perturbational-complexity measures already established in the consciousness literature. Signal entropy, as operationalized by Lempel-Ziv complexity (Schartner et al. 2015) or the perturbational complexity index (Casali et al. 2013), is a property of recorded dynamics in the present. Trajectory entropy, as defined above, is a property of distributions over future state-action paths under a given policy and model. The paper becomes stronger when it insists on that distinction rather than using one word for both.

The key paper-level claim is not that consciousness always minimizes entropy in the abstract. The tighter claim is:

- this paper proposes that conscious access is associated with systems that can shape distributions over future trajectories rather than merely react to present stimuli
- this paper reads different consciousness frameworks as describing different constraints on that shaping process (Friston et al. 2017; Albantakis et al. 2023; Mashour et al. 2020)
- trajectory entropy is introduced here as a candidate bookkeeping variable that makes those constraints comparable

## Four-Module Architecture (Heuristic Correspondence Table)

The following table is a heuristic correspondence, not a consensus unification. It records how this paper reads each existing framework as constraining a particular functional role. The mapping is partial and approximate; it does not derive any one framework from another.

| Module | Formal role | Closest existing framework | Observable proxy | Failure mode |
| --- | --- | --- | --- | --- |
| Generation | Expands candidate policies or hypotheses | Generative-model sampling | candidate-policy diversity, latent branching | deterministic or degenerate candidate set |
| Selection | Chooses among candidates under expected future cost | Active inference (Friston et al. 2017) | policy updates, uncertainty-sensitive choice | random or reward-only choice without epistemic component |
| Integration | Prevents fragmentation across subsystems | IIT-like irreducibility constraint (Albantakis et al. 2023) | perturbational complexity or synergy proxy | local selection without coherent whole-system state |
| Propagation | Makes selected state globally available | GNWT-like broadcast (Mashour et al. 2020) | ignition or cross-area generalization | local success without reportable access |

This table is the heart of the single-file version. Without it, the paper reads like a manifesto. With it, the proposed mapping becomes inspectable and falsifiable.

## Why This Is Not Just A Relabeling

The strongest skeptical response is that the proposed framework is simply active inference (Friston et al. 2017) in a new coat. The right answer is partly yes and partly no.

- yes, selection is very close to policy choice under expected free energy
- yes, the paper borrows existing work rather than replacing it
- no, the four-module decomposition makes explicit how this paper reads integration (Albantakis et al. 2023) and global broadcast (Mashour et al. 2020) as additional constraints on a trajectory-shaping system, constraints that active inference alone does not foreground
- no, the architecture proposes a cleaner dissociation program than any one borrowed theory provides on its own

That means the paper's value is architectural and methodological first, not revolutionary first.

## Verified Toy Example

This repo contains one local result that can live inside the paper without overclaiming: `simulations/branching_navigation_sim.py`.

**Reproduction command:** `python simulations/branching_navigation_sim.py --seed 7 --n_envs 1000 --depth 6 --branching 2 --reward_lo 0 --reward_hi 100 --clue_noise 8.0 --budget 4`

Using 1,000 randomly generated branching environments with depth `6`, branching factor `2`, reward range `[0, 100]`, clue noise `8.0`, and seed `7`, three agents were compared in this toy model:

- a current-branch agent using only local noisy clues
- a budgeted-branch agent with a fixed sample of four counterfactual futures
- a branch-aware agent with exact branch values

Fresh local verification in this repo produced:

| Agent | Mean reward |
| --- | --- |
| Current-branch | 86.985 |
| Budgeted-branch(4) | 91.663 |
| Branch-aware | 98.437 |

Derived comparisons:

- budgeted advantage over current-branch: `4.678`
- full branch-aware advantage over current-branch: `11.452`
- fraction of full gap recovered by budgeted access: `40.851%`
- budgeted win rate over current-branch: `62.4%`

**Scope of this toy result.** This result supports a narrow functional claim only: in this toy branching environment, improved access to counterfactual branch structure improves decision performance. It does not support the paper's stronger mechanistic claims about biological conscious access. The asymmetry should be stated plainly: the functional claim (branch access helps in branching environments) is supported by this simulation; the mechanistic claim (that biological conscious access actually operates as trajectory-entropy reduction) is not supported by this toy model and remains an open empirical question. This is exactly the sort of narrow, non-hyped result the paper should carry.

## Scope and Non-Claims

The paper should say this explicitly.

- It is about reportable conscious access, not the full hard problem.
- It does not derive IIT from trajectory entropy.
- It does not prove GNWT is true.
- It does not show that trajectory entropy can already be measured directly in brains without approximation.
- It does not require Level B of the book to stand as a theory paper.

## Minimal Empirical Program

A publishable version should anchor each major claim to one primary assay rather than several optional ones.

| Claim | Primary assay | What would count against the claim |
| --- | --- | --- |
| Selection predicts reportability better than state entropy alone | masked report plus confidence with explicit model comparison | state entropy or arousal explains reportability equally well or better |
| Propagation and integration can dissociate | global broadcast task plus perturbational complexity proxy | both proxies collapse into the same signal under the supposedly dissociating manipulation |
| Four-module architecture clarifies theory pluralism | preregistered ablation in a toy POMDP | ablations fail to produce the predicted module-specific impairments |

## What Is Computationally Supported

- `simulations/branching_navigation_sim.py` gives the manuscript one verified functional toy example (see Verified Toy Example above for the exact command and seed).
- The repo does not yet contain a dedicated POMDP ablation notebook for the four-module decomposition itself.
- Because of that, this manuscript should currently be presented as a theory-plus-toy-model paper, not as a full empirical theory paper. It does not contain neural evidence, brain-level measurements, or direct support for the mechanistic claims about consciousness.

## Data and Code Availability

For submission, this paper needs only a small reproducible artifact set.

- a toy POMDP or control-as-inference notebook
- one figure script for the module architecture
- one appendix defining how trajectory entropy would be estimated in simulations
- the verified branching toy script (`simulations/branching_navigation_sim.py`) and the exact reproduction command (see Verified Toy Example section above)

## Submission Blockers

- Extend the verified branching toy into an explicit trajectory-entropy computation rather than only a reward comparison.
- Replace any remaining draft `Results` language with `Predictions` or `Derived propositions` unless actual empirical outputs are added. This manuscript has no neural evidence, and its language should reflect that throughout.
- Add a short appendix explaining how the paper borrows from IIT (Albantakis et al. 2023) without inheriting IIT’s strongest metaphysical commitments.
- Finalize citations using primary literature sources. All framework references must point to primary papers: Friston et al. 2017 for active inference, Mashour et al. 2020 for GNWT, Albantakis et al. 2023 for IIT, Melloni et al. 2023 for COGITATE protocol. Replace any remaining internal repo prose, book-draft narrative, or planning-file references used as argumentative support with proper primary citations.
- Add primary complexity/signal-entropy anchors: Schartner et al. 2015 for Lempel-Ziv complexity, Casali et al. 2013 for perturbational complexity index.

## References

- Albantakis, L., Barbosa, L., Findlay, G., Grasso, M., Haun, A. M., Marshall, W., ... & Tononi, G. (2023). Integrated information theory (IIT) 4.0: Formulating the properties of phenomenal existence in physical terms. *PLoS Computational Biology*, 19(10), e1011465. https://doi.org/10.1371/journal.pcbi.1011465
- Casali, A. G., Gosseries, O., Rosanova, M., Boly, M., Sarasso, S., Casali, K. R., ... & Massimini, M. (2013). A theoretically based index of consciousness independent of sensory processing and behavior. *Science Translational Medicine*, 5(198), 198ra105. https://pubmed.ncbi.nlm.nih.gov/23946194/
- Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., & Pezzulo, G. (2017). Active inference: A process theory. *Neural Computation*, 29(1), 1-49. https://pubmed.ncbi.nlm.nih.gov/27870614/
- Mashour, G. A., Roelfsema, P., Changeux, J.-P., & Dehaene, S. (2020). Conscious processing and the global neuronal workspace hypothesis. *Neuron*, 105(5), 776-798. https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/
- Melloni, L., Mudrik, L., Pitts, M., Bendtz, K., Ferrante, O., Gorska, U., ... & Koch, C. (2023). An adversarial collaboration protocol for testing contrasting predictions of global neuronal workspace and integrated information theory. *PLoS ONE*, 18(2), e0268577. https://pubmed.ncbi.nlm.nih.gov/36763595/
- Schartner, M. M., Seth, A. K., Noirhomme, Q., Boly, M., Bruno, M.-A., Laureys, S., & Barrett, A. B. (2015). Complexity of multi-dimensional spontaneous EEG decreases during propofol induced general anaesthesia. *PLoS ONE*, 10(8), e0133532. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0133532
