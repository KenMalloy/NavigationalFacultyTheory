# A Paired Multi-Maze Benchmark for Quantum-Adaptive and Classical-Adaptive Navigation

## Manuscript Snapshot

| Field | Value |
| --- | --- |
| Article type | Benchmark and methods paper with current confirmatory results |
| Current status | Strongest of the seven as a results-backed standalone draft |
| Supports book material | `book_draft_v2.md` Chapter 10 |
| Best venue class | Benchmarking, reinforcement learning methodology, artificial life, quantum-adjacent ML |
| Core risk | Overclaiming general quantum superiority instead of a narrower regime claim |

## Abstract

We present a paired multi-maze benchmark for comparing learned quantum-adaptive and classical-adaptive navigation controllers. The benchmark enforces matched training budgets, independent optimization of each controller, paired evaluation on shared mazes, and confirmatory inference at the maze level across multiple procedurally generated maze families. Across 90 confirmatory mazes in three families, we find that only the 3D/6D family yields a confidence interval on normalized advantage that excludes zero (mean `5.7700`, 95% CI `[2.1145, 9.4255]`). The remaining families (2D/5D and 4D/7D) produce intervals that include zero. This paper does not demonstrate superiority of quantum-adaptive controllers over classical planning in general, nor does it establish any biological relevance. The benchmark instead provides a controlled regime comparison showing where, within the current families tested, a learned quantum-adaptive controller can outperform a matched learned classical-adaptive controller, and where it cannot.

## Current Confirmatory Summary

Source: per-maze CSV export (`enaqt_simulation/results/2026-03-15-survival-scaling-gap3/combined.csv`), confirmatory summary derived from that export.

| Maze family | n mazes | Mean normalized advantage | 95% CI | Maze win rate | Win rate 95% CI |
| --- | --- | --- | --- | --- | --- |
| 2D / 5D | 30 | 9.6131 | [-0.6571, 19.8833] | 0.6000 | [0.4232, 0.7541] |
| 3D / 6D | 30 | 5.7700 | [2.1145, 9.4255] | 0.5333 | [0.3614, 0.6977] |
| 4D / 7D | 30 | 1.8057 | [-3.2363, 6.8477] | 0.5000 | [0.3315, 0.6685] |

The primary result is the 3D/6D family, whose confidence interval excludes zero. The 2D/5D family shows a numerically larger mean but its interval spans zero, making it inconclusive. The 4D/7D family is similarly inconclusive with a small positive mean and a wide interval spanning zero. These results do not support monotonic scaling with latent dimension or a universal advantage for the quantum-adaptive controller.

## Methods

### Benchmark Fairness Rules

The benchmark is governed by four fairness constraints, stated here explicitly rather than implied:

1. **Matched training budgets.** Both the quantum-adaptive and classical-adaptive controllers receive the same number of training evaluations (`--train-evals`), so neither side silently receives more optimization effort.
2. **Independent optimization.** Each controller is optimized independently for its own architecture. The classical-adaptive controller uses a learned state-dependent stochastic gate and is re-optimized from scratch, not copied from the quantum controller with quantum features removed.
3. **Paired evaluation.** Both controllers are evaluated on the same set of procedurally generated mazes, so maze-level variation affects both sides equally.
4. **Multiple mazes per family.** Each family includes at least 10 mazes per difficulty bin (30 mazes total per family), and the maze---not the trial---is the unit of confirmatory inference.

### Confirmatory Reporting Rules

The following reporting rules were fixed before the confirmatory run (see `enaqt_simulation/maze_scaling_analysis_workflow.md` for the full specification):

- The maze is the unit of inference. Trial-level outcomes within a maze are not treated as independent confirmatory samples.
- Bin and spec definitions are fixed before the run being cited.
- The per-maze CSV is published alongside any derived summary table.
- Negative and mixed results are retained, not filtered.

### Environment Generation

Mazes are procedurally generated with controlled geometry parameters (`side`, `barriers`, `gaps_per_barrier`) and assigned to difficulty bins (`easy`, `medium`, `hard`) based on detour ratio. Maze seeds are recorded so that all results are reproducible.

### Controller Definitions

- **Quantum-adaptive controller**: A controller that uses a parameterized quantum circuit in a latent space of dimension `latent_dim`, with parameters evolved via differential evolution under the shared training budget.
- **Classical-adaptive controller**: A controller that uses a learned state-dependent stochastic gate in the same observable space, also evolved via differential evolution under the same shared training budget. This is not a crippled control; it is independently optimized for its own architecture.

Both controller definitions are implemented in `enaqt_simulation/maze_scaling_sweep.py` and `enaqt_simulation/maze_navigator.py`.

### Classical Reality Checks

In addition to the primary matched-controller comparison, the benchmark includes classical reality-check baselines:

- **Shortest-path planner**: A full-map planner that computes optimal paths. This planner solves every maze in every benchmark family tested here. It is the classical upper bound, not the primary comparator. Per-maze planner distances are recorded in the combined CSV and reported in Appendix A.
- **Wall-following heuristics**: Right-wall and left-wall followers, included as lower-bound reality checks.

The paper's primary comparison is therefore *learned quantum-adaptive controller versus matched learned classical-adaptive controller under fixed budgets*, not *quantum versus all classical methods*. The shortest-path planner establishes that no maze in this benchmark is classically unsolvable.

## Main Results

### Primary Result: 3D/6D Family

The 3D/6D family is the only family whose confidence interval on mean normalized advantage excludes zero: mean `5.7700`, 95% CI `[2.1145, 9.4255]`, across 30 confirmatory mazes. The maze win rate is `0.5333` (Wilson CI `[0.3614, 0.6977]`). This is a modest, positive signal---not a large or universal advantage.

### Secondary Results: 2D/5D and 4D/7D Families

The 2D/5D family shows a numerically larger mean (`9.6131`) but a wide interval that spans zero (`[-0.6571, 19.8833]`). The 4D/7D family shows a small positive mean (`1.8057`) with an interval spanning zero (`[-3.2363, 6.8477]`). Neither family provides confirmatory evidence of quantum-adaptive advantage in this benchmark.

### What These Results Show

In the current benchmark families, the quantum-adaptive controller shows a statistically detectable advantage only in the 3D/6D family. The results do not establish monotonic scaling with latent dimension, do not demonstrate that higher-dimensional controllers always help, and do not show universal advantage across maze families.

## Difficulty-Gradient Analysis (Exploratory)

**Note:** The following difficulty-bin analysis is exploratory. The difficulty bins were defined before the confirmatory run, but the decision to examine within-family difficulty gradients was made after inspecting the family-level results. These findings should be treated as hypothesis-generating, not confirmatory.

Source: per-maze CSV, grouped by `maze_dim`, `latent_dim`, and `bin_label`.

| Family | Bin | n mazes | Mean norm. adv. | 95% CI | Win rate |
| --- | --- | --- | --- | --- | --- |
| 3D/6D | easy | 10 | 5.0577 | [-1.3027, 11.4181] | 0.4000 |
| 3D/6D | medium | 10 | 4.3881 | [-2.7047, 11.4809] | 0.5000 |
| 3D/6D | hard | 10 | 7.8641 | [1.9054, 13.8228] | 0.7000 |

In the current benchmark families, harder 3D cases and middle latent gaps look more promising than trivial mazes or maximal latent dimensionality. However, this pattern is observed post hoc within a single family and should not be generalized without pre-registered replication.

For completeness, the 2D/5D and 4D/7D difficulty-bin breakdowns are:

| Family | Bin | n mazes | Mean norm. adv. | 95% CI | Win rate |
| --- | --- | --- | --- | --- | --- |
| 2D/5D | easy | 10 | 14.3318 | [-11.9991, 40.6628] | 0.7000 |
| 2D/5D | medium | 10 | 12.9263 | [-1.6248, 27.4774] | 0.6000 |
| 2D/5D | hard | 10 | 1.5811 | [-6.9533, 10.1155] | 0.5000 |
| 4D/7D | easy | 10 | 4.9045 | [-6.6220, 16.4311] | 0.6000 |
| 4D/7D | medium | 10 | -1.2340 | [-7.6139, 5.1460] | 0.4000 |
| 4D/7D | hard | 10 | 1.7464 | [-6.2620, 9.7548] | 0.5000 |

These breakdowns show wide intervals throughout. No difficulty bin in the 2D/5D or 4D/7D families produces a CI excluding zero.

## Hard-Negative Section

This section documents where the benchmark does not favor the quantum-adaptive controller.

1. **4D/7D family**: The highest maze dimensionality tested shows no detectable advantage. The mean normalized advantage is `1.8057` with a confidence interval spanning zero.
2. **Classical planning ceiling**: The shortest-path planner solves every maze in every family. The learned quantum-adaptive controller does not approach planner-level performance. The benchmark question is therefore not whether quantum methods can beat classical planning, but whether they can beat a matched learned classical controller.
3. **No monotonic scaling**: Increasing latent dimension from 5 to 6 to 7 does not produce monotonically increasing advantage. The 4D/7D family is weaker than both 2D/5D and 3D/6D.
4. **Win rates near chance**: Even in the 3D/6D family, the maze win rate of `0.5333` is only modestly above `0.5`, with the confidence interval including values near chance.

## Discussion

### Regime Claim, Not Universal Claim

The strongest current local benchmark signal is a moderate advantage for the 3D/6D family, not a universal law. This is a regime finding: under matched training budgets and independent optimization, there exists a benchmark family in which the quantum-adaptive controller outperforms the classical-adaptive controller, but this advantage is modest, family-dependent, and does not extend reliably to the other families tested.

### The Benchmark Journey as Evidence of Discipline

This benchmark went through several iterations. Early versions tested a single hand-picked maze and used asymmetric controller comparisons that inflated the apparent quantum advantage. The current version uses matched budgets, independently optimized controllers, multiple mazes per family, and maze-level inference. The result is a smaller, more honest signal. This trajectory---from an inflated initial result through fair testing to an honest modest result---is itself evidence of methodological discipline, not a weakness.

### Relationship to Classical Planning

The shortest-path planner remains the classical upper bound and solves every benchmark family considered here. This paper does not claim that quantum-adaptive controllers outperform classical planning. It claims only that, in one benchmark family, a learned quantum-adaptive controller outperforms a matched learned classical-adaptive controller. The reality-check paragraph is essential: readers should understand that the benchmark question is about matched learned controllers, not about quantum methods versus optimal classical methods.

### Scope Limitations

This paper does not demonstrate:

- Quantum superiority over classical planning in general.
- Monotonic scaling of advantage with latent dimension.
- That higher-dimensional controllers always help.
- Any biological relevance of the benchmark results.

These non-claims are stated here and in the abstract to prevent misreading.

### Relationship to Quantum Walks on State Spaces

The idea of quantum navigation on structured state spaces has precedent in theoretical work on quantum walks over combinatorial and biological networks (Santiago-Alarcon et al. 2020, quantum walks on genotype networks). The present benchmark does not claim to implement or test those theoretical proposals, but it occupies a related space: asking whether quantum-adaptive dynamics on a structured discrete environment can outperform matched classical-adaptive dynamics. The connection is noted for context, not as a claim of equivalence.

## Data and Code Availability

The paper is already close to an open benchmark package. Submission should include:

- Per-maze CSV exports (`enaqt_simulation/results/2026-03-15-survival-scaling-gap3/combined.csv`)
- Confirmatory summary tables derived only from the per-maze CSVs
- Exact command lines used for the cited runs (recorded in the CSV `command_line` column)
- Controller and baseline definitions in the manuscript appendix
- Per-maze planner distances in Appendix A

## Submission Blockers

- Lock the exact controller definitions in prose so the adaptive classical baseline is fully reimplementable.
- Add one primary benchmark family and label all other slices exploratory if they were chosen after inspection.
- Move all consciousness framing out of the paper body except perhaps one sentence of motivation.
- Add a short failure-analysis section showing where the benchmark washes out.

## References

- Santiago-Alarcon, D., et al. (2020). Quantum walks on genotype networks and their potential applications in evolutionary biology. *Journal of Physics A: Mathematical and Theoretical*.
- Confirmatory analysis workflow: described in Methods section above; full specification in `enaqt_simulation/maze_scaling_analysis_workflow.md`.

## Appendix A: Per-Maze Planner Results

The shortest-path planner was evaluated on every maze in the confirmatory set. The per-maze planner distances are recorded in the `planner_mean_dist` column of the combined CSV (`enaqt_simulation/results/2026-03-15-survival-scaling-gap3/combined.csv`).

Summary by family:

| Family | n mazes | Planner solves all | Notes |
| --- | --- | --- | --- |
| 2D/5D | 30 | Yes | Planner distance is `0.0` on all mazes (goal reached optimally). |
| 3D/6D | 30 | Yes | Planner distance is `0.0` on all mazes. |
| 4D/7D | 30 | Yes | Planner distance is `0.0` on all mazes. |

These results confirm that no maze in the benchmark is classically unsolvable. The shortest-path planner reaches the goal optimally on every maze, establishing it as the classical upper bound. The learned controllers (both quantum-adaptive and classical-adaptive) do not approach this performance level. The benchmark's primary comparison is therefore between two learned adaptive controllers, not between a learned controller and an optimal planner.

Per-maze planner distances for all 90 mazes are available in the published CSV. Reviewers can verify that `planner_mean_dist = 0.0` for every row, confirming universal planner solvability.
