# Conscious Processing as Trajectory-Entropy Reduction

## Title

Conscious Processing as Trajectory-Entropy Reduction: A Navigational Synthesis of Active Inference, Integrated Information, and Global Workspace

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Theory and synthesis paper with a verified toy example |
| Current status | Much closer to publishable as a theory-plus-toy-model paper |
| Supports book material | `book_draft_v2.md` Chapters 1, 3, and 4 |
| Best venue class | Consciousness theory, formal cognitive science, philosophy of cognitive science |
| Core risk | The paper overreaches if it implies new empirical confirmation rather than a new organizing frame |

## Abstract

This manuscript should be framed as a theory paper with one modest empirical supplement. Its central claim is that conscious access can be organized as a navigation problem in which a system reduces uncertainty over future trajectories under action and resource constraints. The paper does not replace active inference, Integrated Information Theory, or Global Neuronal Workspace Theory. It instead supplies a modular synthesis that maps active inference onto selection, IIT onto integration, and GNWT onto propagation, while reserving generation as the upstream source of candidate trajectories. A locally verified toy branching simulation shows that access to counterfactual branch structure improves performance in a simple decision environment, which is enough to support the paper's weakest functional claim while leaving the stronger mechanistic claims explicitly open.

## Introduction

The cleanest motivation for this paper is the field's pattern of partial success. Existing consciousness theories often explain different parts of the phenomenon well while failing to close the whole gap. The repo's broader book materials already use the COGITATE result, post-COGITATE methodological critiques, and the structural proximity of IIT-like and GNWT-like cortical territories as motivation for an architectural rather than winner-take-all interpretation. This manuscript should inherit that framing but keep its scope narrow: it is about conscious access, task-level control, and theory decomposition, not about solving the hard problem.

The paper's real claim is architectural. It proposes that a family of successful theories can be read as describing distinct constraints on the same control problem: how a bounded system shapes the distribution of its own future trajectories.

## Contribution

The publishable version of this paper now has four concrete jobs.

1. State that it is a theory-and-synthesis paper rather than a hidden empirical paper.
2. Define trajectory entropy cleanly enough that readers can see what is new and what is only a relabeling.
3. Show exactly where the mapping to IIT and GNWT is constrained rather than total.
4. Use one verified toy model to show that counterfactual branch access is a coherent functional construct rather than metaphorical rhetoric.

## Core Formalism

Let a policy-conditioned trajectory over horizon `H` be `tau = (s_t:t+H, a_t:t+H)`. The paper’s organizing quantity is:

`H_tau(pi) = -E_p(tau | pi, M)[log p(tau | pi, M)]`

where `M` is the internal model used to assign probabilities over future trajectories.

The key paper-level claim is not that consciousness always minimizes entropy in the abstract. The tighter claim is:

- conscious access is associated with systems that can shape distributions over future trajectories rather than merely react to present stimuli
- different consciousness frameworks describe different constraints on that shaping process
- trajectory entropy is the common bookkeeping variable that makes those constraints comparable

This also clarifies the relation to the entropy literature already cited in the broader project. Signal entropy is a property of recorded dynamics in the present. Trajectory entropy is a property of distributions over future state-action paths. The paper becomes stronger when it insists on that distinction rather than using one word for both.

## Four-Module Architecture

| Module | Formal role | Closest existing framework | Observable proxy | Failure mode |
| --- | --- | --- | --- | --- |
| Generation | Expands candidate policies or hypotheses | Generative-model sampling | candidate-policy diversity, latent branching | deterministic or degenerate candidate set |
| Selection | Chooses among candidates under expected future cost | Active inference | policy updates, uncertainty-sensitive choice | random or reward-only choice without epistemic component |
| Integration | Prevents fragmentation across subsystems | IIT-like irreducibility constraint | perturbational complexity or synergy proxy | local selection without coherent whole-system state |
| Propagation | Makes selected state globally available | GNWT-like broadcast | ignition or cross-area generalization | local success without reportable access |

This table is the heart of the single-file version. Without it, the paper reads like a manifesto. With it, the mapping becomes inspectable.

## Why This Is Not Just A Relabeling

The strongest skeptical response is that Level A is simply active inference in a new coat. The right answer is partly yes and partly no.

- yes, selection is very close to policy choice under expected free energy
- yes, the paper borrows existing work rather than replacing it
- no, the four-module decomposition makes explicit how integration and global broadcast constrain a trajectory-shaping system
- no, the architecture creates a cleaner dissociation program than any one borrowed theory provides on its own

That means the paper's value is architectural and methodological first, not revolutionary first.

## Verified Toy Example

This repo now contains one local result that can live inside the paper without overclaiming: `simulations/branching_navigation_sim.py`.

Using 1,000 randomly generated branching environments with depth `6`, branching factor `2`, reward range `[0, 100]`, clue noise `8.0`, and seed `7`, three agents were compared:

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

This toy result does not support the paper's stronger mechanistic claims. It does support the weakest, functional claim: improved access to counterfactual branch structure improves performance in a branching environment. That is exactly the sort of narrow, non-hyped result the paper should carry.

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

## What Is Already Evidenced In This Repo

- The book already contains the cleanest prose version of the architectural claim in `book_draft_v2.md`.
- `simulations/branching_navigation_sim.py` now gives the manuscript one verified functional toy example.
- The repo still does not contain a dedicated POMDP ablation notebook for the four-module decomposition itself.
- Because of that, this manuscript should currently be presented as a theory-plus-toy-model paper, not as a full empirical theory paper.

## Data and Code Availability

For submission, this paper needs only a small reproducible artifact set.

- a toy POMDP or control-as-inference notebook
- one figure script for the module architecture
- one appendix defining how trajectory entropy would be estimated in simulations
- the verified branching toy script and the command needed to reproduce its summary

## Submission Blockers

- Extend the verified branching toy into an explicit trajectory-entropy computation rather than only a reward comparison.
- Replace any draft `Results` language with `Predictions` or `Derived propositions` unless actual outputs are added.
- Add a short appendix explaining how the paper borrows from IIT without inheriting IIT’s strongest metaphysical commitments.
- Finalize citations from the book bibliography and remove all portfolio-era citation artifacts.
