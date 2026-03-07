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

This manuscript should be framed as a benchmark paper about matched adaptive controllers, not as a consciousness paper and not as a proof of universal quantum superiority. The benchmark asks when a learned quantum-adaptive controller outperforms a matched learned classical-adaptive controller under fixed maze families, fixed training budgets, and maze-level confirmatory inference. Current local summaries already support a modest regime claim: across 90 confirmatory mazes, the 3D/6D family shows a positive mean normalized advantage of `5.7700` with interval `[2.1145, 9.4255]`, while 2D/5D and 4D/7D remain weaker or inconclusive. That is enough for a publishable benchmark draft if the manuscript stays disciplined about what it has and has not shown.

## Current Confirmatory Summary

Source: `enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md`

| Maze family | n mazes | Mean normalized advantage | Interval | Maze win rate |
| --- | --- | --- |
| 2D / 5D | 30 | 9.6131 | [-0.6571, 19.8833] | 0.6000 |
| 3D / 6D | 30 | 5.7700 | [2.1145, 9.4255] | 0.5333 |
| 4D / 7D | 30 | 1.8057 | [-3.2363, 6.8477] | 0.5000 |

These results already suggest the right headline: the signal is family-dependent, modest, and strongest in a middle regime rather than at maximal latent dimension.

## Reality Check Against Classical Planning

The benchmark gets more credible, not less, when it states its ceiling clearly. The repo's own benchmark summary already says the shortest-path planner remains the classical upper bound and solves every benchmark family considered here. That means the paper's real comparison is not "quantum versus all classical methods." It is "learned quantum-adaptive controller versus matched learned classical-adaptive controller under fixed budgets." That is still a publishable benchmark question, but only if the manuscript says it outright.

## Benchmark Governance

The paper becomes publishable when it is explicit about fairness.

| Governance item | Current local answer |
| --- | --- |
| Unit of inference | Maze, not trial |
| Confirmatory reporting rule | Fixed in `enaqt_simulation/maze_scaling_analysis_workflow.md` |
| Training budget | Shared budget per benchmark family |
| Baseline family | Learned classical-adaptive baseline plus planner and heuristic reality checks |
| Negative findings | Retained rather than filtered |

The manuscript should quote these rules directly rather than implying them.

## What The Paper Can Honestly Claim

- The benchmark contains real classical baselines rather than only crippled controls.
- The clearest current positive result is a moderate advantage for one benchmark family, not a universal law.
- Harder maze families and medium latent gaps are more promising than trivial mazes or maximal latent dimensionality.
- Classical planning remains the upper bound on the current benchmark.

## What The Paper Should Not Claim

- It does not show quantum superiority over classical planning in general.
- It does not show monotonic scaling with latent dimension.
- It does not show that higher-dimensional controllers always help.
- It does not establish any biological relevance.

## Repo Evidence To Cite In The Paper

- `enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension.md`
- `enaqt_simulation/results/2026-03-15-survival-scaling-gap3/by_dimension_bin.md`
- `enaqt_simulation/maze_scaling_analysis_workflow.md`
- `docs/plans/2026-03-15-quantum-navigation-benchmark-summary.md`

## Recommended Manuscript Structure

1. Benchmark motivation and fairness problem.
2. Environment generation and paired-maze logic.
3. Controller definitions and parameter-budget matching.
4. Confirmatory analysis rule with maze as unit of inference.
5. Main result table.
6. Hard-negative section describing where the benchmark does not favor the quantum controller.
7. Discussion limited to regime claims.
8. Reality-check paragraph clarifying why classical planning is not the primary comparator.

## Data and Code Availability

The paper is already close to an open benchmark package. Submission should include:

- per-maze CSV exports
- confirmatory summary tables derived only from the per-maze CSVs
- exact command lines used for the cited runs
- baseline definitions in the manuscript appendix

## Submission Blockers

- Lock the exact controller definitions in prose so the adaptive classical baseline is fully reimplementable.
- Add one primary benchmark family and label all other slices exploratory if they were chosen after inspection.
- Move all consciousness framing out of the paper body except perhaps one sentence of motivation.
- Add a short failure-analysis section showing where the benchmark washes out.
