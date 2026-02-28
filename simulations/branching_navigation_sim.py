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
