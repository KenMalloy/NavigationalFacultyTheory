## Appendix A: Simulation Code and Results

### Design Principles

The navigation benchmark tests a single question: can evolution build better navigators when the substrate includes quantum resources than when it does not, given the same optimization budget? Everything in the design exists to keep that question honest.

Four fairness rules govern every run:

1. **Matched training budgets.** Both controllers receive the same number of fitness evaluations. The budget is fixed before either controller is evolved. We did not keep training until the quantum controller won.

2. **Independent optimization.** The classical-adaptive controller is not a crippled version of the quantum controller with quantum features removed. It has its own architecture (a learned state-dependent stochastic gate) and is optimized from scratch via differential evolution under the same budget.

3. **Paired evaluation.** Both controllers face identical mazes with identical random seeds, so maze-level variation affects both sides equally. Per-maze advantage is a paired difference.

4. **The maze is the unit of inference.** Each family includes at least 30 mazes. Trial-level outcomes within a maze are not treated as independent confirmatory samples. Confidence intervals are computed at the maze level using normal-approximation SEM intervals, with win rates using Wilson intervals.

These rules were locked before the confirmatory run. Negative and mixed results are retained, not filtered.

### Maze Generation

Mazes are procedurally generated N-dimensional grids with barrier hyperplanes and random gaps. Three parameters control geometry: side length, number of barriers, and gaps per barrier. Difficulty is classified by detour ratio (shortest path length divided by straight-line distance) into easy, medium, and hard bins. All maze seeds are recorded so every result is reproducible.

For the confirmatory set, 3D mazes used side length 9, 6 barrier hyperplanes, and 2 gaps per barrier, producing an average detour ratio of approximately 1.25x.

### Controller Architectures

The **quantum-adaptive controller** operates a parameterized quantum circuit in a latent space of dimension `latent_dim`. At each time step, radical pair spin dynamics in the latent space produce a singlet yield that depends on the agent's conformational state and the local maze geometry. A state-dependent adaptive measurement basis selects which quantum observable to read. The singlet yield biases movement in the physical maze dimensions. Parameters governing the feedback loop, measurement basis selection, and movement weights are evolved via differential evolution.

The **classical-adaptive controller** replaces the quantum circuit with a learned state-dependent stochastic gate operating in the same observable space. It receives identical sensory inputs and has its own independently optimized parameters. This controller is the primary comparator.

Two reality-check baselines are also included: a shortest-path planner with full map knowledge (the classical upper bound) and wall-following heuristics (the lower bound). The planner solves every maze in every family. The benchmark question is therefore not "quantum versus optimal classical planning" but "quantum-adaptive versus matched classical-adaptive under realistic evolutionary constraints."

### Scaling Sweep

We swept maze dimensionality (2D, 3D, 4D) crossed with latent dimensionality (5D, 6D, 7D), producing three families. Each family includes 30 confirmatory mazes (10 per difficulty bin).

**Family-level results (30 mazes each):**

| Family | Mean normalized advantage | 95% CI | Maze win rate |
|---|---|---|---|
| 2D / 5D | +9.61% | [-0.66%, +19.88%] | 60.0% |
| 3D / 6D | +5.77% | [+2.11%, +9.43%] | 53.3% |
| 4D / 7D | +1.81% | [-3.24%, +6.85%] | 50.0% |

Only the 3D/6D family produces a confidence interval that excludes zero. The 2D/5D family shows a larger point estimate but wider uncertainty that spans zero. The 4D/7D family is a wash.

These results do not support monotonic scaling with latent dimension. The effect is non-monotonic, peaking at an intermediate latent gap of approximately 3 extra dimensions.

### The 90-Maze Confirmatory Result

Pooling all 90 mazes across the three families, the overall normalized advantage is +3.3%, 95% CI [+0.9%, +5.8%]. The confidence interval excludes zero.

### Difficulty Stratification (Exploratory)

Within the 3D/6D family, we examined advantage by difficulty bin. This analysis was not pre-registered; it was conducted after inspecting family-level results and should be treated as hypothesis-generating.

| Difficulty | n mazes | Mean norm. advantage | 95% CI | Win rate |
|---|---|---|---|---|
| Easy | 10 | +5.06% | [-1.30%, +11.42%] | 40% |
| Medium | 10 | +4.39% | [-2.70%, +11.48%] | 50% |
| Hard | 10 | +7.86% | [+1.91%, +13.82%] | 70% |

The hard-maze bin is the only stratum whose CI excludes zero. The gradient is suggestive: harder mazes, where detour ratios force more navigational decisions, produce larger quantum advantage. But with 10 mazes per bin, no strong conclusion is warranted.

### Hard Negatives

The 4D/7D family shows no detectable advantage. Win rates near chance appear even in the positive families. The shortest-path planner solves everything. These are features of honest benchmarking, not embarrassments.

### Code Availability

All simulation code is available in the project repository under `enaqt_simulation/`. Key files: `maze_scaling_sweep.py` (scaling benchmark driver), `maze_navigator.py` (controller and baseline implementations), and `core.py` (quantum dynamics building blocks). The per-maze CSV for the confirmatory run is in `enaqt_simulation/results/`. Every command line used for the cited runs is recorded in the CSV's `command_line` column.

---

