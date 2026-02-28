# Appendices to: Consciousness as Navigational Faculty

## Kenneth Malloy — Draft v1.0, March 2026

These appendices accompany the main paper and provide supplementary evidence, technical details, and extended engagement with competing frameworks.

---

## Appendix A: Branching Navigation Simulation Source Code

The following Python script implements the branching tree game described in Section X.A′ of the main paper. It is self-contained, requires only the Python standard library, and is fully reproducible with the default seed (7). Run with `python branching_navigation_sim.py` to reproduce the reported results; use `--help` for parameter options.

```python
#!/usr/bin/env python3
"""
Minimal toy simulation for a branching-game hypothesis.

We compare three agents on the same randomly generated tree:

1. Current-branch agent:
   Sees only the current node's noisy local clues about each child branch.

2. Budgeted-branch agent:
   Sees a limited sample of counterfactual futures under each child branch.

3. Branch-aware agent:
   Knows the true value of every reachable branch and can choose the best one.

This is a Level A / functional toy model. It does not say anything by itself
about quantum substrate or consciousness. It only tests whether access to
counterfactual branch structure improves expected performance in a branching
environment.
"""

from __future__ import annotations

import argparse
import random
import statistics
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Node:
    depth: int
    leaf_reward: float | None = None
    mean_value: float = 0.0
    best_value: float = 0.0
    children: list["Node"] = field(default_factory=list)
    clues: list[float] = field(default_factory=list)
    child_values: list[float] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return not self.children


@dataclass
class StepRecord:
    depth: int
    chosen_action: int
    decision_scores: list[float]
    clues: list[float]
    child_values: list[float]


@dataclass
class PlayResult:
    reward: float
    steps: list[StepRecord]


def build_tree(
    depth: int,
    branching: int,
    rng: random.Random,
    reward_min: float,
    reward_max: float,
    clue_noise: float,
) -> Node:
    if depth == 0:
        reward = rng.uniform(reward_min, reward_max)
        return Node(
            depth=0,
            leaf_reward=reward,
            mean_value=reward,
            best_value=reward,
        )

    children = [
        build_tree(
            depth=depth - 1,
            branching=branching,
            rng=rng,
            reward_min=reward_min,
            reward_max=reward_max,
            clue_noise=clue_noise,
        )
        for _ in range(branching)
    ]

    child_values = [child.best_value for child in children]
    child_means = [child.mean_value for child in children]
    clues = [value + rng.gauss(0.0, clue_noise) for value in child_means]

    return Node(
        depth=depth,
        mean_value=statistics.fmean(child_means),
        best_value=max(child_values),
        children=children,
        clues=clues,
        child_values=child_values,
    )


class CurrentBranchAgent:
    name = "current-branch"

    def score_options(self, node: Node, rng: random.Random) -> list[float]:
        del rng
        return list(node.clues)


class BudgetedBranchAgent:
    def __init__(self, sample_budget: int) -> None:
        if sample_budget < 1:
            raise ValueError("sample_budget must be at least 1")
        self.sample_budget = sample_budget
        self.name = f"budgeted-branch({sample_budget})"

    def score_options(self, node: Node, rng: random.Random) -> list[float]:
        return [
            max(
                node.clues[index],
                max(
                    sample_leaf_reward(child, rng)
                    for _ in range(self.sample_budget)
                ),
            )
            for index, child in enumerate(node.children)
        ]


class BranchAwareAgent:
    name = "branch-aware"

    def score_options(self, node: Node, rng: random.Random) -> list[float]:
        del rng
        return list(node.child_values)


def argmax(values: Sequence[float]) -> int:
    return max(range(len(values)), key=values.__getitem__)


def sample_leaf_reward(node: Node, rng: random.Random) -> float:
    current = node
    while not current.is_leaf:
        current = rng.choice(current.children)
    assert current.leaf_reward is not None
    return current.leaf_reward


def play_game(
    root: Node,
    agent: CurrentBranchAgent | BudgetedBranchAgent | BranchAwareAgent,
    rng: random.Random,
) -> PlayResult:
    steps: list[StepRecord] = []
    node = root

    while not node.is_leaf:
        decision_scores = agent.score_options(node, rng)
        action = argmax(decision_scores)
        steps.append(
            StepRecord(
                depth=node.depth,
                chosen_action=action,
                decision_scores=list(decision_scores),
                clues=list(node.clues),
                child_values=list(node.child_values),
            )
        )
        node = node.children[action]

    assert node.leaf_reward is not None
    return PlayResult(reward=node.leaf_reward, steps=steps)


def summarize_run(
    games: int,
    depth: int,
    branching: int,
    sample_budget: int,
    clue_noise: float,
    seed: int,
    reward_min: float,
    reward_max: float,
) -> None:
    rng = random.Random(seed)
    agents = [
        CurrentBranchAgent(),
        BudgetedBranchAgent(sample_budget),
        BranchAwareAgent(),
    ]
    scores_by_agent = {agent.name: [] for agent in agents}
    example_root: Node | None = None
    example_results: dict[str, PlayResult] = {}

    for game_index in range(games):
        root = build_tree(
            depth=depth,
            branching=branching,
            rng=rng,
            reward_min=reward_min,
            reward_max=reward_max,
            clue_noise=clue_noise,
        )
        game_results = {
            agent.name: play_game(
                root,
                agent,
                random.Random(rng.randrange(1_000_000_000)),
            )
            for agent in agents
        }

        for agent in agents:
            scores_by_agent[agent.name].append(game_results[agent.name].reward)

        if game_index == 0:
            example_root = root
            example_results = game_results

    assert example_root is not None
    assert example_results

    current_name = agents[0].name
    budgeted_name = agents[1].name
    branch_name = agents[2].name

    current_scores = scores_by_agent[current_name]
    budgeted_scores = scores_by_agent[budgeted_name]
    branch_scores = scores_by_agent[branch_name]

    budgeted_advantages = [b - c for b, c in zip(budgeted_scores, current_scores)]
    full_advantages = [b - c for b, c in zip(branch_scores, current_scores)]
    budgeted_wins = sum(b > c for b, c in zip(budgeted_scores, current_scores))
    branch_wins = sum(b > c for b, c in zip(branch_scores, current_scores))
    ties = sum(b == c for b, c in zip(branch_scores, current_scores))

    mean_current = statistics.fmean(current_scores)
    mean_budgeted = statistics.fmean(budgeted_scores)
    mean_branch = statistics.fmean(branch_scores)
    full_gap = mean_branch - mean_current
    recovered = (
        (mean_budgeted - mean_current) / full_gap if full_gap > 0 else float("nan")
    )

    print("Toy branching navigation simulation")
    print("---------------------------------")
    print(f"games           : {games}")
    print(f"depth           : {depth}")
    print(f"branching       : {branching}")
    print(f"sample_budget   : {sample_budget}")
    print(f"clue_noise      : {clue_noise}")
    print(f"reward_range    : [{reward_min}, {reward_max}]")
    print(f"seed            : {seed}")
    print()
    for agent in agents:
        mean_reward = statistics.fmean(scores_by_agent[agent.name])
        print(f"{agent.name:24} mean reward: {mean_reward:8.3f}")
    print()
    print(
        f"{'budgeted advantage':24} : {statistics.fmean(budgeted_advantages):8.3f}"
    )
    print(f"{'full advantage':24} : {statistics.fmean(full_advantages):8.3f}")
    print(f"{'gap recovered':24} : {recovered:8.3%}")
    print(f"{'budgeted win rate':24} : {budgeted_wins / games:8.3%}")
    print(f"{'branch win rate':24} : {branch_wins / games:8.3%}")
    print(f"{'tie rate':24} : {ties / games:8.3%}")
    print()
    print("Example game")
    print("------------")
    print(f"Optimal reachable reward from root: {example_root.best_value:.3f}")
    print()
    print(format_path("Current-branch path", example_results[current_name]))
    print()
    print(format_path("Budgeted-branch path", example_results[budgeted_name]))
    print()
    print(format_path("Branch-aware path", example_results[branch_name]))


def format_path(title: str, result: PlayResult) -> str:
    lines = [title]
    for index, step in enumerate(result.steps):
        score_str = ", ".join(f"{value:6.2f}" for value in step.decision_scores)
        clue_str = ", ".join(f"{value:6.2f}" for value in step.clues)
        value_str = ", ".join(f"{value:6.2f}" for value in step.child_values)
        lines.append(
            f"  step {index:02d} | node depth={step.depth} | "
            f"choose={step.chosen_action} | scores=[{score_str}] | "
            f"clues=[{clue_str}] | "
            f"true_branch_values=[{value_str}]"
        )
    lines.append(f"  final reward: {result.reward:.3f}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal toy simulation of local vs budgeted vs branch-aware agents."
    )
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--branching", type=int, default=2)
    parser.add_argument("--sample-budget", type=int, default=4)
    parser.add_argument("--clue-noise", type=float, default=8.0)
    parser.add_argument("--reward-min", type=float, default=0.0)
    parser.add_argument("--reward-max", type=float, default=100.0)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summarize_run(
        games=args.games,
        depth=args.depth,
        branching=args.branching,
        sample_budget=args.sample_budget,
        clue_noise=args.clue_noise,
        seed=args.seed,
        reward_min=args.reward_min,
        reward_max=args.reward_max,
    )


if __name__ == "__main__":
    main()
```

---

## Appendix B: Non-Neural Evidence for Microtubule-Mediated Navigation

This appendix collects the detailed empirical evidence for proto-navigational behavior in non-neural eukaryotes, summarized in Section III.D of the main text.

### Fungi

Mycelial networks have no neurons, no central nervous system, and no brain. Yet recent work on cord-forming wood-decay fungi reveals nontrivial network-level plasticity across long timescales. Fukasawa et al. (2024; *Fungal Ecology*; doi:10.1016/j.funeco.2024.101387) demonstrated that mycelia responded differently to circle versus cross arrangements of colonized wood blocks, consistent with sensitivity to spatial arrangement — a form of pattern recognition — persisting over months. Related experiments on ecological memory showed that prior resource encounters bias subsequent growth and migration: when a mycelium discovered a food source and was then placed in a fresh environment, it emerged from the same side of the starting block that had previously led to reward — spatial memory in an organism without a single neuron (Fukasawa, Savoury & Boddy, 2020; *ISME Journal*; doi:10.1038/s41396-019-0536-3). Electrical signal transfer across mycelial networks shows information-sharing properties analogous to neural transmission, though this remains a methodologically challenging and active empirical field. Money (2021; *Fungal Biology*; doi:10.1016/j.funbio.2021.02.001) has articulated conceptual arguments for "hyphal and mycelial consciousness," though this remains controversial and the evidence is best characterized as history-dependent, adaptive network behavior rather than consciousness in any phenomenal sense.

### Slime Molds

Physarum polycephalum solves mazes (Nakagaki et al., 2000), optimizes transport networks in ways comparable to human-designed infrastructure (Tero et al., 2010), anticipates periodic stimuli (Saigusa et al., 2008), and exhibits habituation — a form of learning previously thought to require neurons (Boisseau, Vogel & Dussutour, 2016). Critically, Physarum's cognitive functions are mediated by its cytoskeletal microtubule networks, with the topology of both actin and tubulin cytoskeletal networks implicated in how computation occurs within them. The observation that slime mold memory traces are overwritable in light of new, salient information meets accepted criteria for genuine navigational memory.

### Plants

The "plant neurobiology" movement, while controversial, has documented electrical signaling, adaptive behavior, and learning in organisms with no neural tissue (Calvo et al., 2020). Plant cells are among the most microtubule-rich eukaryotic cells, with elaborate cortical microtubule arrays that reorganize dynamically in response to environmental stimuli.

### Significance for NFT

These cases matter for NFT because standard computational theories of consciousness cannot account for them: if consciousness requires neurons, synapses, and global workspace broadcasting, then fungal and slime mold cognition must be dismissed as "mere" chemistry. If consciousness requires microtubule-mediated quantum coupling to possibility space, then these organisms' cognitive capacities — and their limitations (no temporal self-awareness, no abstract reasoning) — follow directly from the lower complexity and dimensionality of their microtubule networks relative to cortical architectures.

---

## Appendix C: Entropy Taxonomy

The main text employs several distinct entropy-related concepts. Because these are related but not interchangeable, this appendix specifies which notion is doing what work in the paper, to prevent the appearance of sliding between formal vocabularies.

### C.1. Thermodynamic Entropy (Boltzmann/Gibbs)

The entropy of the second law. It defines the arrow of time and the gradient along which NFT claims consciousness navigates (Section II.B). When the paper says "entropy provides the current" or "the entropy gradient," this is the notion in play. It is a property of macrostates, measured in units of energy per temperature, and it increases monotonically in isolated systems.

### C.2. Shannon Entropy

The information-theoretic measure of uncertainty in a probability distribution: H(X) = −Σ p(x) log p(x). This is the standard measure for quantifying unpredictability of neural signals and is the baseline against which Tsallis and Rényi measures are compared. When the paper discusses the entropic brain hypothesis (Carhart-Harris et al., 2014; Carhart-Harris, 2018), the empirical measure is Shannon entropy applied to EEG power spectra or signal complexity.

### C.3. Tsallis Entropy

A one-parameter generalization of Shannon entropy: S_q = (1/(q−1))(1 − Σ p(x)^q), where q is the non-extensivity parameter. For q = 1, Tsallis reduces to Shannon. For q > 1, the measure is sensitive to heavy-tailed distributions and long-range correlations — exactly the statistical signatures of systems at criticality. When the paper claims that neural dynamics exhibit "non-extensive entropy" or that the Tsallis q-parameter is a diagnostic marker (Section IX.G, Marker 1), this is the operative measure. The claim is that conscious brain dynamics have q significantly greater than 1, reflecting the non-independent, scale-free structure of neural activity.

### C.4. Rényi Entropy

Another one-parameter generalization: H_α = (1/(1−α)) log(Σ p(x)^α). Like Tsallis, it reduces to Shannon for α → 1 and is sensitive to the tails of the distribution. The paper uses Rényi entropy primarily in the context of EEG analysis (Section II.B) and the Rényi entropy-complexity causality space (Section VI.E). The relationship between Tsallis and Rényi is monotonic: S_q and H_α carry the same ordinal information for matched parameters, but their additivity properties differ (Tsallis is non-additive for independent subsystems; Rényi is additive).

### C.5. Algorithmic (Kolmogorov) Complexity

The length of the shortest program that produces a given string. This is a property of individual objects, not distributions, and it is uncomputable in general. The paper engages it primarily in Section VI.D (the DeLancey critique) and Section VI.E (the AIT evolution). The key limitation for NFT's purposes is that Kolmogorov complexity is time-symmetric: K(x) ≈ K(reverse(x)), which makes it structurally incapable of addressing temporal directionality.

### C.6. Free Energy (Fristonian)

Variational free energy F = E_q[log q(θ) − log p(o, θ)] is an upper bound on surprise (negative log model evidence). It is not an entropy measure per se but a functional that combines entropy of the approximate posterior with expected energy. When the paper says "minimizing free energy *is* navigating possibility space" (Section II.B), the claim is that Friston's optimization objective can be reinterpreted as a special case of NFT's navigational operation — specifically, the selection component biased by the energy landscape E(x) on the hypercube (Section VIII.E).

### C.7. Trajectory Entropy (Chen & Sanders)

The entropy over distributions of future trajectories, as formalized in the CER model (Chen & Sanders, 2025). This is the most specific entropy concept in the paper: it measures how much a system's future is compressed given its goals and current state. Conscious systems, on NFT's account, reduce trajectory entropy more efficiently than classical systems because quantum interference on the hypercube provides polynomial-vs-exponential search speedup (Section III.B, IX.G Marker 5).

### C.8. Negative Conditional von Neumann Entropy

A quantum information quantity that can be negative — something classically forbidden — and implies entanglement between system and observer (Cerf & Adami, 1997). Its thermodynamic consequence (del Rio et al., 2011) is that an observer entangled with a system can extract more work during erasure than the Landauer limit permits, providing a physically grounded bound that no classical system can cross. This is invoked in Section IX.G Marker 5 as a theoretical ceiling that conscious (quantum-coupled) systems might approach.

### How These Relate

The paper's argument moves across these notions deliberately, not interchangeably. Thermodynamic entropy (C.1) provides the navigational gradient. Shannon/Tsallis/Rényi (C.2–C.4) provide the empirical measurement tools. Algorithmic complexity (C.5) is engaged and critiqued as insufficient. Free energy (C.6) is reinterpreted rather than replaced. Trajectory entropy (C.7) and negative conditional entropy (C.8) are the quantities most specific to NFT's mechanistic claims. A reviewer who objects that "the paper uses entropy loosely" should find this taxonomy sufficient to evaluate whether each usage is justified on its own terms.

---

## Appendix D: Extended Engagement with Competing Frameworks

The main text engages with IWMT, the Free Energy Principle, dimensional approaches, and strong physicalism (Sections VI.A–VI.E). This appendix provides more detailed engagement with additional competing frameworks identified by reviewers as requiring direct response.

### D.1. Predictive Processing and Active Inference

Predictive processing (PP) and its active inference extension (Parr, Pezzulo & Friston, 2022) are arguably NFT's strongest classical competitors. A PP advocate can restate NFT's core claim in their own vocabulary: "You call it navigation through possibility space; I call it policy selection under a generative model." The restatement is not trivial — it identifies a genuine overlap.

Hodson, Mehta, and Smith (2024) provide a useful benchmark: in their systematic review, predictive coding has modest empirical support and active inference remains promising but under-tested against alternatives. This means the competitor is serious but not triumphant — exactly the kind of rival that demands explicit differentiation.

NFT's response rests on three points where the frameworks diverge:

*First*, the substrate question. PP/active inference is substrate-independent by construction — it can run on any system that performs approximate Bayesian inference, including classical digital hardware. NFT makes a specific substrate commitment: navigation requires genuine quantum indeterminacy at the microtubule level. The Level 2 vs. Level 3 experiment (Section X.G) is designed to adjudicate exactly this: if classical systems at criticality perform indistinguishably from quantum systems, PP wins and NFT's substrate commitment is falsified.

*Second*, the temporal question. PP treats time as a background parameter — the dimension along which predictions unfold. It works *in* time but does not account *for* time. NFT treats temporal experience as the primary phenomenon: the felt flow of time is what navigation through possibility space feels like from the inside. PP has no explanation for why there is a subjective "now" or why time feels directional; NFT derives both from the entropy gradient and the navigational process.

*Third*, the novelty question. PP predicts that organisms minimize surprise — they seek expected states. NFT allows consciousness to be genuinely exploratory — navigating toward novel regions of possibility space when the entropy gradient favors it. The entropic brain data (Carhart-Harris et al., 2014; Carhart-Harris, 2018; Frohlich et al., 2022) showing that expanded consciousness involves increased entropy, not decreased surprise, is more naturally accommodated by NFT than by PP, though predictive processing advocates have proposed "relaxed beliefs" models to handle this.

### D.2. Recurrent Processing Theory

Recurrent processing theory (RPT) holds that conscious perception requires recurrent (feedback) processing in cortical circuits, while feedforward processing alone produces unconscious responses. Recent work in rapid object recognition (Motlagh et al., 2024) shows divergence between conscious and unconscious processing around ~180 ms, consistent with the timing at which recurrent feedback loops engage.

RPT overlaps with NFT in one important respect: both theories require that conscious processing involves information flowing in loops rather than just feedforward cascades. NFT's "integration" component (IIT's Φ) and RPT's recurrent requirement are structurally similar — both demand that the system's current state be influenced by its own prior processing.

Where they diverge: RPT is a purely classical neural theory. It makes no substrate commitment beyond "cortical neurons with feedback connections." NFT predicts that recurrent processing is necessary but not sufficient — the recurrent loops must operate on a quantum-coupled substrate to produce genuine navigation rather than classical information processing. The discriminative prediction: if recurrent processing in a classical neuromorphic system (Level 2) produces the same behavioral and physiological signatures as recurrent processing in a quantum-coupled system (Level 3), RPT is sufficient and NFT's additional commitment is unnecessary.

### D.3. Quantum Cognition Without Quantum Brain

This is a crucial distinction the paper must confront directly. Quantum cognition — the use of quantum probability formalism to model decision-making phenomena like conjunction fallacies, order effects, and interference — has genuine empirical traction (Pothos & Busemeyer, 2022). But its proponents do not thereby commit to quantum computation in the brain. The formalism works as a mathematical tool regardless of whether the underlying hardware is quantum mechanical.

NFT's Marker 3 (Section IX.G) directly addresses this: it predicts that human decision data should satisfy specific quantum probability constraints (the QQ equality, the reciprocity law) while LLM outputs should violate them. But if LLM outputs *also* satisfy these constraints — because the constraints reflect statistical structure in training data rather than quantum substrate physics — then quantum cognition provides no support for NFT's Level B claim. The constraints would be "quantum-like" without being "quantum."

NFT's honest position: quantum cognition evidence supports Level A (consciousness has formal properties well-described by quantum probability) but not Level B (those properties arise from physical quantum processes in the brain). The jump from formal description to physical mechanism requires the independent microtubule evidence and the Level 2 vs. Level 3 experiment — quantum cognition alone cannot make it.

### D.4. Hard Criteria for Theories of Consciousness

Doerig, Schurger, and Herzog (2021) argue that consciousness science has too many incompatible theories partly because empirical constraints are too weak. Their "hard criteria" framework demands that theories make predictions that can distinguish them from structurally different alternatives — not just predict phenomena that multiple theories can accommodate.

NFT is explicitly designed to meet this challenge. The split between "supportive but not uniquely discriminative" and "uniquely discriminative" predictions in Section X is a direct response to the hard criteria program. NFT's scientific credibility rests on the discriminative predictions (X.C, X.D, X.G, X.H, X.J), not on the supportive ones (X.A, X.B, X.E, X.F). If the discriminative predictions fail, the theory fails — regardless of how many supportive observations it can accommodate.

We note, however, that Doerig et al.'s criteria cut against many theories, not just NFT. IIT, GNWT, and RPT all face versions of the same challenge. NFT's advantage, if it has one, is that its discriminative predictions are unusually specific: they predict outcomes at the microtubule level (spectral regime, decoherence times, back-action evasion) that no competing theory predicts, providing clear falsification targets.

### D.5. GNWT's Post-COGITATE Response

The main text relies on the COGITATE adversarial collaboration (2025) to motivate NFT's synthesis, arguing that neither IIT nor GNWT emerged with full confirmation. Naccache et al. (2025) have published a response on behalf of the GNWT framework, arguing that: (a) several nontrivial GNWT predictions were in fact supported by the COGITATE data; (b) the decisive conscious-vs-unconscious contrast that GNWT proponents regard as central was not tested in the COGITATE protocol; and (c) the "partial failure" framing overstates the degree to which GNWT was challenged.

NFT's position: Naccache et al.'s response is reasonable and should be taken seriously. The COGITATE results do not falsify GNWT — they challenge specific predictions while leaving the core framework intact. NFT does not require GNWT to be wrong; it requires GNWT to be incomplete. The specific claim is that GNWT describes the broadcasting mechanism (propagation) but not the navigational process (generation + selection) or the substrate coupling (Orch OR interface). Even if all of GNWT's core predictions are eventually confirmed, this would be consistent with NFT's claim that broadcasting is a necessary subsystem of a larger navigational architecture. The question is whether broadcasting is the whole story or part of a larger one.

---

## Appendix E: Microtubule-Anesthesia Complications

The main text presents the microtubule-anesthesia evidence (Khan et al., 2024; Craddock et al., 2015, 2017) as suggestive support for the quantum substrate hypothesis. This appendix notes a complication that strengthens the evidence's realism while complicating its interpretation.

Li et al. (2025; *BMC Anesthesiology, 25*, 109; doi:10.1186/s12871-025-02956-9) found that different microtubule-modulating drugs shifted isoflurane sensitivity in mice in different directions: epothilone D and vinblastine increased sensitivity (leftward LORR shift, lower EC50), while paclitaxel produced a marginal rightward shift (decreased sensitivity). This suggests the microtubule/anesthesia relationship is real — it is experimentally reproducible and pharmacologically specific — but mechanistically messier than a simple "stabilize microtubules → resist anesthesia" narrative. The relationship between microtubule dynamics and anesthetic sensitivity likely involves multiple binding sites, conformational effects, and dose-dependent nonlinearities.

For NFT, this is informative rather than threatening. The theory predicts that microtubule *quantum coupling* matters, not that microtubule *stability* per se determines consciousness. A drug that stabilizes microtubules in a conformation that enhances quantum coupling would delay anesthesia; a drug that stabilizes microtubules in a conformation that disrupts coupling might not. The Li et al. result motivates the need for spectroscopic measurements of quantum effects under different modulators (as proposed in Section X.C), rather than relying solely on behavioral endpoints.
