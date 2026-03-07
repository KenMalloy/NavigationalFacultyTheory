## Chapter 10: The Navigation Benchmark

Theory proposes. Simulation tests. And then the simulation must survive scrutiny. This chapter tells the story of a computational demonstration that began with a dramatic headline, failed to survive fair testing, was rebuilt from scratch, and produced a more honest result that is, in some ways, more interesting than the one it replaced.

### The First Result

The original simulation placed agents on a six-dimensional hypercube (64 vertices) and projected their behavior into a two-dimensional maze. A genetic algorithm evolved parameters governing the feedback loop and movement weights. Four conditions were compared: quantum dynamics with adaptive measurement and evolved parameters, quantum with fixed measurement basis, classical stochastic dynamics with the same evolved parameters, and quantum with random parameters.

On a serpentine 8x8 maze, the quantum+evolved agent found the goal in 24% of runs. Every other condition achieved 0%. The result was striking: a categorical separation between quantum-adaptive and everything else.

But the result had a methodological flaw. The genetic algorithm optimized parameters for the quantum+adaptive condition, and those same parameters were handed to the controls. The controls were running parameters tuned for a different dynamical regime. And no competent classical strategy (shortest-path planning, wall-following) was tested. The "classical" comparator was not classical intelligence. It was quantum-optimized parameters running without quantum dynamics.

### Why It Didn't Survive

We introduced fair classical baselines: a shortest-path planner with full map knowledge, wall-following heuristics, and independently re-optimized controllers for each condition. The shortest-path planner solved every maze. The re-optimized classical controllers largely closed the gap that had appeared so dramatic in the original comparison.

The original headline collapsed. This was the right outcome. A result that cannot survive fair testing was never a result.

### Rebuilding the Benchmark

We rebuilt the simulation framework around four principles:

**Matched training budgets.** Both quantum-adaptive and classical-adaptive controllers receive the same number of fitness evaluations during optimization. Neither side gets a hidden advantage from extra computation. The budget was locked before we saw results. We did not keep evolving until the quantum controller won.

**Independent optimization.** Each controller is evolved for its own dynamical regime. The classical controller has its own learned state-dependent stochastic gate, not quantum parameters with the quantum dynamics stripped out.

**Paired evaluation.** On each maze, the quantum and classical controllers face identical random trajectories (same seeds), so common noise cancels. The per-maze advantage is a paired difference, not two independent estimates.

**Multiple mazes.** Results are averaged across many randomly generated mazes within a family, not cherry-picked from a single favorable instance.

### The Scaling Search

We tested whether quantum navigational advantage scales with problem complexity by sweeping maze and latent dimensions: 2D mazes with 6D latent dynamics, 3D mazes with 7D latent dynamics, and 4D mazes with 8D latent dynamics. Each uses barrier hyperplanes with random gaps, generating mazes that are always solvable but structurally varied.

The scaling was not monotonic. 2D/6D showed negligible advantage. 3D/7D showed a moderate positive signal. 4D/8D was weak and inconsistent, likely because the 4D search space exceeds what the optimizer can explore within the training budget.

We then held the maze at 3D and swept latent dimensionality from 3D through 9D. The advantage peaked at an intermediate latent gap of approximately 3 extra dimensions (3D maze with 6D latent state) and declined on both sides. Too few extra dimensions provides insufficient room for interference effects to sculpt probabilities. Too many produces an interference pattern too complex for the optimizer to exploit. The optimum is intermediate.

This non-monotonic pattern mirrors the ENAQT regime from Chapter 8: too little quantum coherence does not help, too much does not help, the advantage lives at an intermediate optimum. The probability sculpting thesis predicts exactly this shape, and the simulation produces it independently.

### The 3D/6D Result

On harder 3D mazes (side length 9, 6 barrier hyperplanes, 2 gaps per barrier, average detour ratio 1.25x), the 3D/6D configuration produced the clearest signal.

In a 10-maze paired run with 100 evaluation trials per maze, the quantum-adaptive controller won on 9 mazes, tied on 1 (an exact tie: 0 advantage, 100 tied trials out of 100), and lost on none. The normalized advantage was +13.0% of path length with a standard error of 4.6%. The per-trial win rate was 52.9%: on any given run, the quantum agent barely edges out the classical agent. But the edge is systematic: it appears on 9 of 10 independent mazes.

We were excited. A 90% maze win rate and +13% advantage looked like a clear signal. The confirmatory run brought the numbers back to earth, which is what confirmatory runs are for.

Across 90 mazes (30 per difficulty bin), with the training budget locked and no re-evolution after seeing which mazes favored which controller, the results were:

| Measure | Value | 95% CI |
|---|---|---|
| Normalized advantage | +3.32% | [+0.87%, +5.77%] |
| Maze win rate | 53.3% | [43.1%, 63.3%] |

The confidence interval excludes zero. The effect is real, modest, and systematic.

Stratified by maze difficulty (detour ratio), the advantage trends upward: +2.68% on easy mazes, +3.43% on medium, +3.85% on hard. The maze-level win rate follows the same gradient: 40%, 57%, 63%. But with 30 mazes per bin, no individual stratum reaches significance on its own. The difficulty gradient is suggestive, not established. A proper test would require substantially more mazes per bin.

### The Compass Pattern

The most important feature of these results is not the magnitude of the advantage but its structure.

A 3.3% survival lift is small on any single decision. A 53% trial win rate is barely above chance. If the question is "does quantum dramatically outperform classical on this maze?" the answer is no. But that is not the question evolution asks.

Evolution asks: across many environments, over many generations, does this mechanism provide a *consistent directional bias*? A compass does not need to be dramatically more accurate than guessing. It needs to point roughly north more often than it points south. A 1% fitness advantage can fix an allele in a population in a few thousand generations.

The 10-maze run shows 52.9% per-trial wins but 90% per-maze wins. The quantum agent does not overwhelm the classical agent on any given trial. It modestly outperforms it on almost every maze. This is exactly the pattern natural selection exploits: a small, systematic bias that compounds across environments and generations. The quantum mechanism does not provide omniscience. It provides a compass.

### What the Shortest-Path Planner Means

The shortest-path planner, which has complete knowledge of the maze, solves every benchmark. This means the quantum-adaptive controller does not achieve "quantum advantage" in the computational sense of outperforming the best possible classical algorithm.

But this comparison is biologically meaningless. Evolution does not have access to a full map of the fitness landscape. It optimizes controllers under constraints: limited generations, limited information about the environment, no foreknowledge of which decisions will matter. The relevant question for NFT is not "can quantum beat omniscient classical planning?" It is "can evolution build better navigators when the biological substrate includes quantum resources than when it does not, given the same optimization budget?"

The benchmark answers this question. Under matched evolutionary constraints, the quantum-coupled controller systematically outperforms the classical controller. We call this *quantum navigational advantage*: not supremacy over all classical strategies, but a systematic edge under the conditions that actually obtain in biological evolution [B].

### What the Simulation Does and Does Not Prove

The simulation demonstrates that a learned quantum-adaptive controller, using radical pair spin dynamics with state-dependent measurement feedback, can systematically outperform a matched learned classical-adaptive controller across multiple randomly generated 3D mazes. The advantage is modest (+3.3%), systematic (CI excludes zero across 90 mazes), and peaks at an intermediate latent dimensionality consistent with the probability sculpting thesis.

The simulation does not prove that the brain implements this mechanism. It does not prove that radical pair spin states in microtubules operate on a state space with the right structure. It does not prove that the amplification from criticality is sufficient in biological tissue. These remain empirical questions.

What the simulation provides is a fair test of the core claim: that evolution, given quantum resources and adaptive measurement, can build controllers that navigate better than evolution without quantum resources, under the same constraints. Both controllers received the same optimization budget, fixed in advance. Neither was re-evolved after results were inspected. The 90-maze confirmatory set was run once. The answer, on this benchmark, is yes. Whether the same holds in biological tissue is the question the experimental program of Chapter 15 is designed to answer. The complete benchmark specification, including maze generation, controller architectures, optimization protocols, and statistical analysis, is reported in [Malloy, "Quantum Navigational Advantage in Evolved 3D Maze Controllers," forthcoming] [B].

**Where we are.** Take a breath. The hardest technical stretch is behind you.

Here is what we have established so far. Quantum and classical probability are categorically different: quantum systems sculpt interference patterns, classical systems roll weighted dice. The original excitonic mechanism failed at body temperature, but radical pair spin coherence works, with a 12.7% yield difference persisting for microseconds. The transduction chain from molecule to neuron is tight but viable, gated by superoxide concentration. A computational benchmark, rebuilt from scratch after its first version failed fair testing, shows that evolution with quantum resources builds better navigators than evolution without them. The advantage is modest (+3.3%) but systematic, exactly the kind of small consistent bias that natural selection exploits.

The mechanism is on the table. Now we ask: what does it explain about the *experience* of consciousness? Why does focus feel different from mind-wandering? Why does pain feel different from pleasure? How does distributed neural activity become unified experience? The next three chapters tackle these questions, and they connect physics to phenomenology in ways that are, I think, genuinely surprising.
