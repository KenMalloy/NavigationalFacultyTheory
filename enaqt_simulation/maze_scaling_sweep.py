"""
Scaling sweep for higher-dimensional maze navigation.

Goal: test whether a learned quantum+adaptive controller gains an advantage
over a re-optimized classical controller as maze dimensionality increases,
without hand-picking a single favorable benchmark.

Methodology is held constant across dimension pairs:
  - same controller family
  - same optimizer class
  - same fitness metric
  - same informed classical planner upper bound
  - same maze family construction
  - same optimization-evaluation budget per condition

Default sweep:
  2D maze / 6D internal state
  3D maze / 7D internal state
  4D maze / 8D internal state

The maze family uses axis-aligned barrier hyperplanes with random gaps. That
avoids the main confound of simple random-wall percolation in high dimensions,
where instances are usually either almost-open or disconnected.
"""

import argparse
import csv
import time
from collections import deque
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import differential_evolution

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from enaqt_simulation.maze_navigator import build_operators, build_H, compute_PS


DEFAULT_SPECS = (
    {"maze_dim": 2, "latent_dim": 6, "side": 8, "barriers": 4, "gaps_per_barrier": 4, "seed": 101},
    {"maze_dim": 3, "latent_dim": 7, "side": 6, "barriers": 4, "gaps_per_barrier": 8, "seed": 202},
    {"maze_dim": 4, "latent_dim": 8, "side": 5, "barriers": 4, "gaps_per_barrier": 12, "seed": 303},
)
DEFAULT_SPEC_MAP = {spec["maze_dim"]: spec for spec in DEFAULT_SPECS}
DEFAULT_DIFFICULTY_BINS = (
    {"label": "near-optimal", "min_detour": 1.00, "max_detour": 1.10},
    {"label": "moderate", "min_detour": 1.10, "max_detour": 1.30},
    {"label": "hard", "min_detour": 1.30, "max_detour": float("inf")},
)
DEFAULT_OPS = build_operators()
DEFAULT_B_FIELD = 50e-6
DEFAULT_A_BASE = 10.0
DEFAULT_J_BASE = 0.0


def parse_int_list(raw):
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def parse_detour_bound(raw):
    token = raw.strip().lower()
    if token in {"inf", "+inf", "infinity", "+infinity"}:
        return float("inf")
    value = float(token)
    if not np.isfinite(value):
        raise ValueError(f"Detour bound must be finite or 'inf', got {raw!r}")
    return value


def parse_difficulty_bins(raw):
    if raw is None:
        return None
    if raw.strip().lower() == "default":
        return tuple(dict(bin_spec) for bin_spec in DEFAULT_DIFFICULTY_BINS)

    bins = []
    seen_labels = set()
    prev_upper = None
    for part in raw.split(","):
        entry = part.strip()
        if not entry:
            continue
        if "=" not in entry or ":" not in entry:
            raise ValueError(
                "Difficulty bins must use label=min:max entries, "
                f"got {entry!r}"
            )
        label, bounds = entry.split("=", 1)
        min_raw, max_raw = bounds.split(":", 1)
        label = label.strip()
        if not label:
            raise ValueError(f"Difficulty bin label cannot be empty in {entry!r}")
        if label in seen_labels:
            raise ValueError(f"Duplicate difficulty bin label: {label!r}")
        lower = parse_detour_bound(min_raw)
        upper = parse_detour_bound(max_raw)
        if lower < 0:
            raise ValueError(
                f"Detour bin lower bound must be >= 0 for {label!r}, got {lower}"
            )
        if upper <= lower:
            raise ValueError(
                f"Detour bin upper bound must be > lower bound for {label!r}"
            )
        if prev_upper is not None and lower < prev_upper:
            raise ValueError(
                "Difficulty bins must be non-overlapping and sorted by lower bound"
            )
        bins.append(
            {"label": label, "min_detour": float(lower), "max_detour": float(upper)}
        )
        seen_labels.add(label)
        prev_upper = upper

    if not bins:
        raise ValueError("At least one difficulty bin must be provided")
    return tuple(bins)


def format_detour_bound(value):
    return "inf" if np.isinf(value) else f"{value:.2f}"


def format_difficulty_bin(bin_spec):
    upper_bracket = "]" if np.isinf(bin_spec["max_detour"]) else ")"
    return (
        f"{bin_spec['label']}=[{format_detour_bound(bin_spec['min_detour'])}:"
        f"{format_detour_bound(bin_spec['max_detour'])}{upper_bracket}"
    )


def classify_detour_bin(detour_ratio, difficulty_bins):
    if difficulty_bins is None:
        return None
    for bin_spec in difficulty_bins:
        lower = bin_spec["min_detour"]
        upper = bin_spec["max_detour"]
        in_bin = lower <= detour_ratio
        if np.isinf(upper):
            if in_bin:
                return bin_spec["label"]
        elif in_bin and detour_ratio < upper:
            return bin_spec["label"]
    return None


def active_mazes_per_bin(args):
    if args.mazes_per_bin is not None:
        return args.mazes_per_bin
    return args.mazes_per_spec


def build_specs(args):
    if args.latent_dims and args.latent_offsets:
        raise ValueError("Choose either --latent-dims or --latent-offsets, not both")

    if args.maze_dims:
        maze_dims = parse_int_list(args.maze_dims)
    else:
        maze_dims = [spec["maze_dim"] for spec in DEFAULT_SPECS]

    specs = []
    for maze_dim in maze_dims:
        if maze_dim not in DEFAULT_SPEC_MAP:
            raise ValueError(
                f"No default maze specification for maze_dim={maze_dim}. "
                f"Available dims: {sorted(DEFAULT_SPEC_MAP)}"
            )

    if args.latent_dims:
        latent_dims = parse_int_list(args.latent_dims)
        mode_desc = f"latent-dims={latent_dims}"
        for maze_dim in maze_dims:
            base = DEFAULT_SPEC_MAP[maze_dim]
            for latent_dim in latent_dims:
                if latent_dim < maze_dim:
                    raise ValueError(
                        f"latent_dim={latent_dim} must be >= maze_dim={maze_dim}"
                    )
                spec = dict(base)
                spec["latent_dim"] = latent_dim
                specs.append(spec)
    elif args.latent_offsets:
        offsets = parse_int_list(args.latent_offsets)
        mode_desc = f"latent-offsets={offsets}"
        for maze_dim in maze_dims:
            base = DEFAULT_SPEC_MAP[maze_dim]
            for offset in offsets:
                latent_dim = maze_dim + offset
                if latent_dim < maze_dim:
                    raise ValueError(
                        f"offset={offset} yields latent_dim={latent_dim} < maze_dim={maze_dim}"
                    )
                spec = dict(base)
                spec["latent_dim"] = latent_dim
                specs.append(spec)
    else:
        specs = [dict(DEFAULT_SPEC_MAP[maze_dim]) for maze_dim in maze_dims]
        mode_desc = "default-scaling"

    geometry_parts = []
    if args.side_override is not None:
        geometry_parts.append(f"side={args.side_override}")
    if args.barriers_override is not None:
        geometry_parts.append(f"barriers={args.barriers_override}")
    if args.gaps_override is not None:
        geometry_parts.append(f"gaps={args.gaps_override}")
    if geometry_parts:
        for spec in specs:
            if args.side_override is not None:
                spec["side"] = args.side_override
            if args.barriers_override is not None:
                spec["barriers"] = args.barriers_override
            if args.gaps_override is not None:
                spec["gaps_per_barrier"] = args.gaps_override
        mode_desc = f"{mode_desc} | " + ", ".join(geometry_parts)

    specs.sort(key=lambda spec: (spec["maze_dim"], spec["latent_dim"]))
    return tuple(specs), mode_desc


def start_goal(maze_dim, side):
    return (0,) * maze_dim, (side - 1,) * maze_dim


def manhattan_nd(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def nd_moves(maze_dim):
    moves = []
    for axis in range(maze_dim):
        step = [0] * maze_dim
        step[axis] = 1
        moves.append(tuple(step))
        step = [0] * maze_dim
        step[axis] = -1
        moves.append(tuple(step))
    return tuple(moves)


def add_coords(a, b):
    return tuple(x + y for x, y in zip(a, b))


def in_bounds(coord, side):
    return all(0 <= value < side for value in coord)


def bfs_distance_map_nd(maze):
    side = maze.shape[0]
    maze_dim = maze.ndim
    start, goal = start_goal(maze_dim, side)
    dist_map = np.full(maze.shape, -1, dtype=int)
    if maze[goal]:
        return dist_map

    moves = nd_moves(maze_dim)
    dist_map[goal] = 0
    queue = deque([goal])
    while queue:
        coord = queue.popleft()
        base = dist_map[coord]
        for move in moves:
            nxt = add_coords(coord, move)
            if in_bounds(nxt, side) and maze[nxt] == 0 and dist_map[nxt] == -1:
                dist_map[nxt] = base + 1
                queue.append(nxt)
    return dist_map


def make_barrier_maze_nd(maze_dim, side, barriers, gaps_per_barrier, seed,
                         min_shortest=None, max_attempts=1000):
    """Construct a generic, solvable N-D barrier maze.

    Each barrier is a full hyperplane orthogonal to one axis, punctured by a
    fixed number of random gates. Cycling across axes gives each dimension a
    comparable amount of obstacle structure without hand-coding a privileged
    route for the quantum controller.
    """
    if side < 4:
        raise ValueError("Barrier mazes need side >= 4")

    start, goal = start_goal(maze_dim, side)
    target_shortest = min_shortest if min_shortest is not None else manhattan_nd(start, goal)
    rng = np.random.default_rng(seed)

    for _ in range(max_attempts):
        maze = np.zeros((side,) * maze_dim, dtype=np.uint8)

        for barrier_idx in range(barriers):
            axis = barrier_idx % maze_dim
            barrier_coord = int(rng.integers(1, side - 1))
            selector = [slice(None)] * maze_dim
            selector[axis] = barrier_coord
            maze[tuple(selector)] = 1

            for _ in range(gaps_per_barrier):
                gate = [int(rng.integers(0, side)) for _ in range(maze_dim)]
                gate[axis] = barrier_coord
                maze[tuple(gate)] = 0

        maze[start] = 0
        maze[goal] = 0
        dist_map = bfs_distance_map_nd(maze)
        if dist_map[start] >= target_shortest:
            return maze, dist_map

    raise RuntimeError(
        f"Could not generate a solvable {maze_dim}D barrier maze after {max_attempts} attempts"
    )


def compute_maze_metrics(spec, maze, dist_map):
    maze_dim = spec["maze_dim"]
    side = spec["side"]
    start, goal = start_goal(maze_dim, side)
    shortest = int(dist_map[start])
    manhattan = int(manhattan_nd(start, goal))
    detour_ratio = float(shortest / max(manhattan, 1))
    open_fraction = float(1.0 - maze.mean())
    return {
        "shortest": shortest,
        "manhattan": manhattan,
        "detour_ratio": detour_ratio,
        "open_fraction": open_fraction,
    }


def make_maze_record(spec, maze_seed):
    maze, dist_map = make_barrier_maze_nd(
        spec["maze_dim"], spec["side"], spec["barriers"], spec["gaps_per_barrier"], maze_seed
    )
    metrics = compute_maze_metrics(spec, maze, dist_map)
    action_targets = {}
    pos_norm = {}
    side_scale = max(spec["side"] - 1, 1)
    moves = nd_moves(spec["maze_dim"])
    for coord_array in np.argwhere(maze == 0):
        coord = tuple(int(value) for value in coord_array)
        targets = [None] * (2 * spec["maze_dim"])
        for action_idx, move in enumerate(moves):
            nxt = add_coords(coord, move)
            if in_bounds(nxt, spec["side"]) and maze[nxt] == 0:
                targets[action_idx] = nxt
        action_targets[coord] = tuple(targets)
        pos_norm[coord] = coord_array.astype(float) / side_scale
    record = dict(spec)
    record.update(metrics)
    record.update(
        {
            "maze_seed": maze_seed,
            "maze": maze,
            "dist_map": dist_map,
            "runtime_context": {
                "start": (0,) * spec["maze_dim"],
                "goal": (spec["side"] - 1,) * spec["maze_dim"],
                "shortest": metrics["shortest"],
                "action_targets": action_targets,
                "pos_norm": pos_norm,
            },
            "bin_label": None,
            "candidate_index": None,
        }
    )
    return record


def select_precommitted_maze_records(spec, args):
    base_seed = spec["seed"]
    difficulty_bins = args.difficulty_bins_parsed
    if not difficulty_bins:
        records = []
        for maze_idx in range(args.mazes_per_spec):
            record = make_maze_record(spec, base_seed + maze_idx)
            record["selection_index"] = maze_idx
            records.append(record)
        return records, {
            "selection_mode": "default",
            "candidate_seeds_scanned": len(records),
        }

    per_bin_target = active_mazes_per_bin(args)
    selected_by_bin = {bin_spec["label"]: [] for bin_spec in difficulty_bins}
    candidate_seeds_scanned = 0

    for candidate_idx in range(args.bin_max_candidates):
        maze_seed = base_seed + candidate_idx
        candidate_seeds_scanned += 1
        record = make_maze_record(spec, maze_seed)
        bin_label = classify_detour_bin(record["detour_ratio"], difficulty_bins)
        if bin_label is None or len(selected_by_bin[bin_label]) >= per_bin_target:
            continue
        record["bin_label"] = bin_label
        record["candidate_index"] = candidate_idx
        selected_by_bin[bin_label].append(record)
        if all(len(selected_by_bin[bin_spec["label"]]) >= per_bin_target for bin_spec in difficulty_bins):
            break

    deficits = {
        bin_spec["label"]: per_bin_target - len(selected_by_bin[bin_spec["label"]])
        for bin_spec in difficulty_bins
        if len(selected_by_bin[bin_spec["label"]]) < per_bin_target
    }
    if deficits:
        deficit_desc = ", ".join(f"{label}: need {count}" for label, count in deficits.items())
        raise RuntimeError(
            "Could not fill all precommitted detour bins within the candidate cap "
            f"for {spec['maze_dim']}D/{spec['latent_dim']}D after "
            f"{candidate_seeds_scanned} candidate seeds ({deficit_desc})."
        )

    ordered_records = []
    selection_index = 0
    for bin_spec in difficulty_bins:
        label = bin_spec["label"]
        for record in selected_by_bin[label]:
            record["selection_index"] = selection_index
            ordered_records.append(record)
            selection_index += 1

    return ordered_records, {
        "selection_mode": "difficulty-bins",
        "difficulty_bins": difficulty_bins,
        "mazes_per_bin": per_bin_target,
        "candidate_seeds_scanned": candidate_seeds_scanned,
        "candidate_limit": args.bin_max_candidates,
        "selected_by_bin": selected_by_bin,
    }


def print_precommitted_manifest(spec, manifest):
    if manifest["selection_mode"] != "difficulty-bins":
        return

    print("\n  Precommitted difficulty-bin manifest")
    print(
        f"    Target: {manifest['mazes_per_bin']} maze(s)/bin | "
        f"candidate cap={manifest['candidate_limit']} | "
        f"scanned={manifest['candidate_seeds_scanned']}"
    )
    for bin_spec in manifest["difficulty_bins"]:
        label = bin_spec["label"]
        selected = manifest["selected_by_bin"][label]
        print(f"    {format_difficulty_bin(bin_spec)}")
        for record in selected:
            print(
                f"      seed={record['maze_seed']:>6d} | candidate={record['candidate_index']:>4d} | "
                f"shortest={record['shortest']:>4d} | detour={record['detour_ratio']:.2f}x | "
                f"open={record['open_fraction']:.2f}"
            )


def choose_bfs_move_nd(coord, maze, dist_map, moves):
    best = None
    best_dist = None
    side = maze.shape[0]
    for idx, move in enumerate(moves):
        nxt = add_coords(coord, move)
        if not in_bounds(nxt, side) or maze[nxt] != 0:
            continue
        cand = dist_map[nxt]
        if cand < 0:
            continue
        if best_dist is None or cand < best_dist:
            best = (idx, nxt)
            best_dist = cand
    return best


def run_shortest_path_planner_nd(maze, dist_map):
    side = maze.shape[0]
    maze_dim = maze.ndim
    _, goal = start_goal(maze_dim, side)
    moves = nd_moves(maze_dim)
    coord = (0,) * maze_dim
    positions = [coord]
    max_steps = np.prod(maze.shape) * 4

    for _ in range(max_steps):
        if coord == goal:
            break
        best = choose_bfs_move_nd(coord, maze, dist_map, moves)
        if best is None:
            break
        _, coord = best
        positions.append(coord)

    reached_goal = coord == goal
    return dist_map[coord], len(positions) - 1, reached_goal, positions


def summarize_values(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("Cannot summarize an empty list of values")
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    sem = float(std / np.sqrt(arr.size)) if arr.size > 1 else 0.0
    return mean, std, sem


def summarize_trials(trials):
    dists = [trial[0] for trial in trials]
    path_lengths = [trial[1] for trial in trials if trial[2]]
    goals_reached = sum(1 for trial in trials if trial[2])
    mean_dist, std_dist, sem_dist = summarize_values(dists)
    if path_lengths:
        mean_path, std_path, sem_path = summarize_values(path_lengths)
    else:
        mean_path = std_path = sem_path = float("inf")
    n_trials = len(trials)
    goal_rate = goals_reached / n_trials
    goal_sem = float(np.sqrt(goal_rate * (1.0 - goal_rate) / n_trials))
    return {
        "mean_dist": mean_dist,
        "std": std_dist,
        "sem": sem_dist,
        "goal_rate": goal_rate,
        "goal_sem": goal_sem,
        "min_dist": int(np.min(dists)),
        "mean_path": mean_path,
        "path_std": std_path,
        "path_sem": sem_path,
        "min_path": int(min(path_lengths)) if path_lengths else float("inf"),
        "n_trials": n_trials,
    }


def compare_paired_trials(quantum_trials, classical_trials, shortest):
    if len(quantum_trials) != len(classical_trials):
        raise ValueError("Quantum and classical trials must have the same length")

    raw_advantages = []
    normalized_advantages_pct = []
    quantum_wins = 0
    classical_wins = 0
    ties = 0

    for quantum_trial, classical_trial in zip(quantum_trials, classical_trials):
        quantum_dist, quantum_path, quantum_goal, _ = quantum_trial
        classical_dist, classical_path, classical_goal, _ = classical_trial
        raw_advantage = classical_dist - quantum_dist
        raw_advantages.append(raw_advantage)
        normalized_advantages_pct.append(100.0 * raw_advantage / max(shortest, 1))

        if quantum_dist < classical_dist:
            quantum_wins += 1
        elif classical_dist < quantum_dist:
            classical_wins += 1
        elif quantum_goal and classical_goal:
            if quantum_path < classical_path:
                quantum_wins += 1
            elif classical_path < quantum_path:
                classical_wins += 1
            else:
                ties += 1
        else:
            ties += 1

    raw_mean, raw_std, raw_sem = summarize_values(raw_advantages)
    norm_mean, norm_std, norm_sem = summarize_values(normalized_advantages_pct)
    n_pairs = len(raw_advantages)
    quantum_win_rate = quantum_wins / n_pairs
    quantum_win_sem = float(np.sqrt(quantum_win_rate * (1.0 - quantum_win_rate) / n_pairs))
    classical_win_rate = classical_wins / n_pairs

    return {
        "raw_advantage_mean": raw_mean,
        "raw_advantage_std": raw_std,
        "raw_advantage_sem": raw_sem,
        "normalized_advantage_pct_mean": norm_mean,
        "normalized_advantage_pct_std": norm_std,
        "normalized_advantage_pct_sem": norm_sem,
        "quantum_win_count": quantum_wins,
        "classical_win_count": classical_wins,
        "ties": ties,
        "quantum_win_rate": quantum_win_rate,
        "quantum_win_sem": quantum_win_sem,
        "classical_win_rate": classical_win_rate,
        "n_pairs": n_pairs,
    }


def make_projections(state_dim, seed):
    rng = np.random.default_rng(seed)
    projections = []
    for _ in range(3):
        vec = rng.normal(size=state_dim)
        vec /= np.linalg.norm(vec)
        projections.append(vec)
    return tuple(projections)


def compute_gradient_nd(ops, B, a_base, J_base, alpha, beta, gamma_mod, projections,
                        state_dim, tau=1.0):
    p_singlet = ops["P_S"]
    proj_a, proj_j, proj_phi = projections

    def ps_at(state):
        a_mhz = a_base + alpha * float(np.dot(proj_a, state))
        j_mhz = J_base + beta * float(np.dot(proj_j, state))
        phi = gamma_mod * float(np.dot(proj_phi, state))
        H = build_H(ops, B, a_mhz, j_mhz, phi)
        return compute_PS(H, p_singlet, tau)

    state0 = np.zeros(state_dim)
    ps0 = ps_at(state0)
    grad = np.zeros(state_dim)
    eps = 0.01
    for idx in range(state_dim):
        plus = state0.copy()
        minus = state0.copy()
        plus[idx] = eps
        minus[idx] = -eps
        grad[idx] = (ps_at(plus) - ps_at(minus)) / (2 * eps)
    return ps0, grad


def compute_classical_gate(state, alpha, beta, gamma_mod, projections):
    proj_a, proj_j, proj_phi = projections
    control = (
        alpha * float(np.dot(proj_a, state)) +
        beta * float(np.dot(proj_j, state)) +
        gamma_mod * float(np.dot(proj_phi, state))
    )
    # Give the classical baseline a learned, state-dependent stochastic gate
    # instead of a fixed 50/50 coin flip.
    return float(np.clip(0.5 + 0.49 * np.tanh(control), 0.01, 0.99))


def unpack_params(params, latent_dim, maze_dim):
    state_dim = latent_dim + maze_dim
    action_dim = 2 * maze_dim
    split0 = latent_dim
    split1 = split0 + latent_dim
    split2 = split1 + 3
    delta_S = params[:split0]
    delta_T = params[split0:split1]
    alpha, beta, gamma_mod = params[split1:split2]
    move_weights = params[split2:].reshape(action_dim, state_dim)
    return delta_S, delta_T, alpha, beta, gamma_mod, move_weights


def parameter_count(latent_dim, maze_dim):
    state_dim = latent_dim + maze_dim
    action_dim = 2 * maze_dim
    return (2 * latent_dim) + 3 + (action_dim * state_dim)


def maxiter_for_budget(latent_dim, maze_dim, popsize, train_evals):
    n_params = parameter_count(latent_dim, maze_dim)
    evals_per_generation = popsize * n_params
    return max(1, (train_evals // evals_per_generation) - 1)


def run_controller_nd(rng, dist_map, runtime_context, latent_dim, projections, delta_S, delta_T,
                      alpha, beta, gamma_mod, ps0, grad, move_weights, gate_mode):
    goal = runtime_context["goal"]
    theta = np.zeros(latent_dim)
    coord = runtime_context["start"]
    state = np.empty(latent_dim + len(goal), dtype=float)
    reached_goal = False
    path_length = 0
    shortest = runtime_context["shortest"]
    n_steps = max(200, shortest * 12)

    for _ in range(n_steps):
        if coord == goal:
            reached_goal = True
            break

        pos_norm = runtime_context["pos_norm"][coord]
        state[:latent_dim] = theta
        state[latent_dim:] = pos_norm

        if gate_mode == "quantum":
            ps = np.clip(ps0 + np.dot(grad, state), 0.01, 0.99)
        elif gate_mode == "classical":
            ps = compute_classical_gate(state, alpha, beta, gamma_mod, projections)
        else:
            raise ValueError(f"Unsupported gate mode: {gate_mode}")

        if rng.random() < ps:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

        state[:latent_dim] = theta
        scores = move_weights @ state
        order = np.argsort(-scores)
        moved = False
        targets = runtime_context["action_targets"][coord]
        for action_idx in order:
            nxt = targets[action_idx]
            if nxt is not None:
                coord = nxt
                path_length += 1
                moved = True
                if coord == goal:
                    reached_goal = True
                break
        if not moved or reached_goal:
            break

    return dist_map[coord], path_length, reached_goal, None


def fitness_fn_nd(params, ops, B, a_base, J_base, dist_map, runtime_context, latent_dim, projections,
                  n_seeds, base_seed, gate_mode):
    delta_S, delta_T, alpha, beta, gamma_mod, move_weights = unpack_params(
        params, latent_dim, dist_map.ndim
    )
    if gate_mode == "quantum":
        ps0, grad = compute_gradient_nd(
            ops, B, a_base, J_base, alpha, beta, gamma_mod, projections,
            latent_dim + dist_map.ndim
        )
    else:
        ps0, grad = None, None

    total = 0.0
    for seed_idx in range(n_seeds):
        rng = np.random.default_rng(base_seed + seed_idx)
        total += run_controller_nd(
            rng, dist_map, runtime_context, latent_dim, projections, delta_S, delta_T,
            alpha, beta, gamma_mod, ps0, grad, move_weights, gate_mode
        )[0]
    return total / n_seeds


def evaluate_controller_nd(params, ops, B, a_base, J_base, dist_map, runtime_context, latent_dim,
                           projections, n_runs, base_seed, gate_mode):
    delta_S, delta_T, alpha, beta, gamma_mod, move_weights = unpack_params(
        params, latent_dim, dist_map.ndim
    )
    if gate_mode == "quantum":
        ps0, grad = compute_gradient_nd(
            ops, B, a_base, J_base, alpha, beta, gamma_mod, projections,
            latent_dim + dist_map.ndim
        )
    else:
        ps0, grad = None, None
    trials = []
    for run_idx in range(n_runs):
        rng = np.random.default_rng(base_seed + run_idx)
        trials.append(
            run_controller_nd(
                rng, dist_map, runtime_context, latent_dim, projections, delta_S, delta_T,
                alpha, beta, gamma_mod, ps0, grad, move_weights, gate_mode
            )
        )
    return summarize_trials(trials)


def evaluate_paired_controllers_nd(
    quantum_params,
    classical_params,
    ops,
    B,
    a_base,
    J_base,
    dist_map,
    runtime_context,
    latent_dim,
    projections,
    n_runs,
    base_seed,
):
    quantum_delta_S, quantum_delta_T, quantum_alpha, quantum_beta, quantum_gamma, quantum_move_weights = unpack_params(
        quantum_params, latent_dim, dist_map.ndim
    )
    classical_delta_S, classical_delta_T, classical_alpha, classical_beta, classical_gamma, classical_move_weights = unpack_params(
        classical_params, latent_dim, dist_map.ndim
    )

    quantum_ps0, quantum_grad = compute_gradient_nd(
        ops, B, a_base, J_base, quantum_alpha, quantum_beta, quantum_gamma, projections,
        latent_dim + dist_map.ndim
    )

    quantum_trials = []
    classical_trials = []
    for run_idx in range(n_runs):
        run_seed = base_seed + run_idx
        quantum_rng = np.random.default_rng(run_seed)
        classical_rng = np.random.default_rng(run_seed)
        quantum_trials.append(
            run_controller_nd(
                quantum_rng, dist_map, runtime_context, latent_dim, projections,
                quantum_delta_S, quantum_delta_T, quantum_alpha, quantum_beta, quantum_gamma,
                quantum_ps0, quantum_grad, quantum_move_weights, "quantum"
            )
        )
        classical_trials.append(
            run_controller_nd(
                classical_rng, dist_map, runtime_context, latent_dim, projections,
                classical_delta_S, classical_delta_T, classical_alpha, classical_beta, classical_gamma,
                None, None, classical_move_weights, "classical"
            )
        )

    quantum_summary = summarize_trials(quantum_trials)
    classical_summary = summarize_trials(classical_trials)
    paired_summary = compare_paired_trials(
        quantum_trials, classical_trials, runtime_context["shortest"]
    )
    return quantum_summary, classical_summary, paired_summary


def evolve_controller_nd(label, ops, B, a_base, J_base, dist_map, runtime_context, latent_dim,
                         projections, n_seeds_ga, ga_maxiter, popsize, seed, gate_mode,
                         de_workers):
    maze_dim = dist_map.ndim
    state_dim = latent_dim + maze_dim
    action_dim = 2 * maze_dim
    bounds = (
        [(-0.2, 0.2)] * latent_dim +
        [(-0.2, 0.2)] * latent_dim +
        [(0.0, 5.0), (0.0, 3.0), (0.0, 0.5)] +
        [(-1.0, 1.0)] * (action_dim * state_dim)
    )
    t0 = time.time()
    result = differential_evolution(
        fitness_fn_nd,
        bounds=bounds,
        args=(ops, B, a_base, J_base, dist_map, runtime_context, latent_dim, projections,
              n_seeds_ga, seed + 1000, gate_mode),
        maxiter=ga_maxiter,
        popsize=popsize,
        seed=seed,
        tol=1e-6,
        polish=False,
        disp=False,
        workers=de_workers,
        updating="deferred" if de_workers != 1 else "immediate",
    )
    elapsed = time.time() - t0
    shortest = runtime_context["shortest"]
    print(
        f"    {label:<18} | best mean dist = {result.fun:5.2f}/{shortest:<3d} | "
        f"{elapsed:5.1f}s"
    )
    return result.x


def print_2d_maze(maze):
    for row in maze:
        print("  " + " ".join("█" if cell else "·" for cell in row))


def aggregate_metric(per_maze, agent_key, metric):
    values = [maze_result[agent_key][metric] for maze_result in per_maze]
    mean, std, sem = summarize_values(values)
    return {"mean": mean, "std": std, "sem": sem}


def aggregate_per_maze_results(per_maze):
    quantum_stats = aggregate_metric(per_maze, "quantum", "mean_dist")
    classical_stats = aggregate_metric(per_maze, "classical", "mean_dist")
    planner_stats = aggregate_metric(per_maze, "planner", "mean_dist")
    shortest_mean, shortest_std, shortest_sem = summarize_values(
        [maze_result["shortest"] for maze_result in per_maze]
    )
    detour_mean, detour_std, detour_sem = summarize_values(
        [maze_result["detour_ratio"] for maze_result in per_maze]
    )
    advantage_mean, advantage_std, advantage_sem = summarize_values(
        [maze_result["paired"]["raw_advantage_mean"] for maze_result in per_maze]
    )
    norm_adv_mean, norm_adv_std, norm_adv_sem = summarize_values(
        [maze_result["paired"]["normalized_advantage_pct_mean"] for maze_result in per_maze]
    )
    q_win_mean, q_win_std, q_win_sem = summarize_values(
        [maze_result["paired"]["quantum_win_rate"] for maze_result in per_maze]
    )
    n_mazes = len(per_maze)
    maze_wins = int(sum(maze_result["paired"]["raw_advantage_mean"] > 0 for maze_result in per_maze))
    total_trial_pairs = int(sum(maze_result["paired"]["n_pairs"] for maze_result in per_maze))
    total_trial_q_wins = int(sum(maze_result["paired"]["quantum_win_count"] for maze_result in per_maze))
    total_trial_c_wins = int(sum(maze_result["paired"]["classical_win_count"] for maze_result in per_maze))
    total_trial_ties = int(sum(maze_result["paired"]["ties"] for maze_result in per_maze))
    return {
        "maze_dim": per_maze[0]["maze_dim"],
        "latent_dim": per_maze[0]["latent_dim"],
        "n_mazes": n_mazes,
        "shortest_mean": shortest_mean,
        "shortest_std": shortest_std,
        "shortest_sem": shortest_sem,
        "detour_mean": detour_mean,
        "detour_std": detour_std,
        "detour_sem": detour_sem,
        "quantum_mean": quantum_stats["mean"],
        "quantum_std": quantum_stats["std"],
        "quantum_sem": quantum_stats["sem"],
        "classical_mean": classical_stats["mean"],
        "classical_std": classical_stats["std"],
        "classical_sem": classical_stats["sem"],
        "planner_mean": planner_stats["mean"],
        "planner_std": planner_stats["std"],
        "planner_sem": planner_stats["sem"],
        "advantage_mean": advantage_mean,
        "advantage_std": advantage_std,
        "advantage_sem": advantage_sem,
        "norm_advantage_mean": norm_adv_mean,
        "norm_advantage_std": norm_adv_std,
        "norm_advantage_sem": norm_adv_sem,
        "trial_quantum_win_rate_mean": q_win_mean,
        "trial_quantum_win_rate_std": q_win_std,
        "trial_quantum_win_rate_sem": q_win_sem,
        "maze_quantum_wins": maze_wins,
        "maze_quantum_win_rate": maze_wins / n_mazes,
        "trial_quantum_wins": total_trial_q_wins,
        "trial_classical_wins": total_trial_c_wins,
        "trial_ties": total_trial_ties,
        "trial_pairs": total_trial_pairs,
    }


def aggregate_per_bin_results(per_maze, difficulty_bins):
    per_bin = []
    for bin_spec in difficulty_bins:
        label = bin_spec["label"]
        bin_results = [maze_result for maze_result in per_maze if maze_result["bin_label"] == label]
        if not bin_results:
            continue
        aggregate = aggregate_per_maze_results(bin_results)
        aggregate["bin_label"] = label
        aggregate["bin_min_detour"] = bin_spec["min_detour"]
        aggregate["bin_max_detour"] = bin_spec["max_detour"]
        per_bin.append(aggregate)
    return tuple(per_bin)


def run_single_maze(maze_record, args, maze_idx, total_mazes):
    maze_dim = maze_record["maze_dim"]
    latent_dim = maze_record["latent_dim"]
    side = maze_record["side"]
    barriers = maze_record["barriers"]
    gaps_per_barrier = maze_record["gaps_per_barrier"]
    maze_seed = maze_record["maze_seed"]
    maze = maze_record["maze"]
    dist_map = maze_record["dist_map"]
    runtime_context = maze_record["runtime_context"]
    shortest = maze_record["shortest"]
    detour_ratio = maze_record["detour_ratio"]
    open_fraction = maze_record["open_fraction"]
    n_params = parameter_count(latent_dim, maze_dim)
    ga_maxiter = (
        args.ga_maxiter
        if args.ga_maxiter is not None
        else maxiter_for_budget(latent_dim, maze_dim, args.popsize, args.train_evals)
    )
    effective_evals = (ga_maxiter + 1) * args.popsize * n_params

    projections = make_projections(latent_dim + maze_dim, maze_seed + 17)
    manifest_suffix = ""
    if maze_record.get("bin_label") is not None:
        manifest_suffix = (
            f" | bin={maze_record['bin_label']} | candidate={maze_record['candidate_index']}"
        )

    print("\n" + "-" * 88)
    print(
        f"  Maze {maze_idx + 1}/{total_mazes} | "
        f"{maze_dim}D maze / {latent_dim}D controller | "
        f"side={side} | barriers={barriers} | gaps/barrier={gaps_per_barrier} | "
        f"shortest={shortest} | detour={detour_ratio:.2f}x | "
        f"open={open_fraction:.2f} | seed={maze_seed}{manifest_suffix}"
    )
    print("=" * 88)
    if maze_dim == 2:
        print_2d_maze(maze)

    ops = DEFAULT_OPS
    B = DEFAULT_B_FIELD
    a_base = DEFAULT_A_BASE
    J_base = DEFAULT_J_BASE

    print(
        f"  Re-optimizing controllers | params={n_params} | maxiter={ga_maxiter} | "
        f"budget~{effective_evals} evals/condition"
    )
    quantum_params = evolve_controller_nd(
        "Quantum+Adaptive", ops, B, a_base, J_base, dist_map, runtime_context, latent_dim,
        projections, args.n_seeds_ga, ga_maxiter, args.popsize, maze_seed + 1, "quantum",
        args.de_workers
    )
    classical_params = evolve_controller_nd(
        "Classical+Adaptive", ops, B, a_base, J_base, dist_map, runtime_context, latent_dim,
        projections, args.n_seeds_ga, ga_maxiter, args.popsize, maze_seed + 2, "classical",
        args.de_workers
    )

    eval_seed = maze_seed + 10000
    quantum, classical, paired = evaluate_paired_controllers_nd(
        quantum_params, classical_params, ops, B, a_base, J_base, dist_map, runtime_context,
        latent_dim, projections, args.n_runs, eval_seed
    )
    planner = summarize_trials([run_shortest_path_planner_nd(maze, dist_map)])

    advantage = paired["raw_advantage_mean"]
    norm_advantage = paired["normalized_advantage_pct_mean"]
    result = {
        "maze_dim": maze_dim,
        "latent_dim": latent_dim,
        "side": side,
        "barriers": barriers,
        "gaps_per_barrier": gaps_per_barrier,
        "maze_seed": maze_seed,
        "candidate_index": maze_record.get("candidate_index"),
        "effective_train_evals": effective_evals,
        "shortest": int(shortest),
        "detour_ratio": float(detour_ratio),
        "open_fraction": float(open_fraction),
        "bin_label": maze_record.get("bin_label"),
        "quantum": quantum,
        "classical": classical,
        "planner": planner,
        "paired": paired,
        "advantage": float(advantage),
        "norm_advantage": float(norm_advantage),
        "quantum_wins": 1 if advantage > 0 else 0,
    }

    print("  Results")
    print(
        f"    Quantum+Adaptive   | mean dist {quantum['mean_dist']:5.2f} +/- "
        f"{quantum['sem']:.2f} SEM | goal {quantum['goal_rate']:6.1%} +/- "
        f"{quantum['goal_sem']:.1%} | best {quantum['min_dist']:2d}"
    )
    print(
        f"    Classical+Adaptive | mean dist {classical['mean_dist']:5.2f} +/- "
        f"{classical['sem']:.2f} SEM | goal {classical['goal_rate']:6.1%} +/- "
        f"{classical['goal_sem']:.1%} | best {classical['min_dist']:2d}"
    )
    print(
        f"    ShortestPathPlan   | mean dist {planner['mean_dist']:5.2f} +/- "
        f"{planner['sem']:.2f} SEM | goal {planner['goal_rate']:6.1%} | "
        f"path {planner['min_path']:2d}"
    )
    print(
        f"    Quantum advantage  | classical - quantum = {paired['raw_advantage_mean']:+.2f} "
        f"+/- {paired['raw_advantage_sem']:.2f} SEM | path closed "
        f"{paired['normalized_advantage_pct_mean']:+.1f}% +/- "
        f"{paired['normalized_advantage_pct_sem']:.1f}% | trial wins "
        f"{paired['quantum_win_count']}/{paired['n_pairs']} "
        f"({paired['quantum_win_rate']:.1%}, ties {paired['ties']})"
    )
    return result


def run_spec(spec, args):
    maze_dim = spec["maze_dim"]
    latent_dim = spec["latent_dim"]

    print("\n" + "=" * 88)
    print(f"  SPEC: {maze_dim}D maze / {latent_dim}D controller")
    print("=" * 88)
    selected_records, manifest = select_precommitted_maze_records(spec, args)
    print_precommitted_manifest(spec, manifest)

    if args.plan_bins_only:
        print("  Plan-bins-only mode: manifest locked; skipping controller optimization.")
        return None

    per_maze = [
        run_single_maze(record, args, maze_idx, len(selected_records))
        for maze_idx, record in enumerate(selected_records)
    ]
    aggregate = aggregate_per_maze_results(per_maze)
    aggregate["spec_id"] = (
        f"{maze_dim}D/{latent_dim}D"
        f"|side={spec['side']}|barriers={spec['barriers']}|gaps={spec['gaps_per_barrier']}"
    )
    aggregate["selection_mode"] = manifest["selection_mode"]
    aggregate["per_maze"] = per_maze
    if manifest["selection_mode"] == "difficulty-bins":
        aggregate["per_bin"] = aggregate_per_bin_results(per_maze, manifest["difficulty_bins"])

    print("\n  Aggregate over mazes")
    print(
        f"    Shortest / detour    | {aggregate['shortest_mean']:.1f} +/- "
        f"{aggregate['shortest_sem']:.1f} SEM | detour {aggregate['detour_mean']:.2f}x +/- "
        f"{aggregate['detour_sem']:.2f} SEM"
    )
    print(
        f"    Quantum+Adaptive   | mean dist {aggregate['quantum_mean']:.2f} +/- "
        f"{aggregate['quantum_sem']:.2f} SEM"
    )
    print(
        f"    Classical+Adaptive | mean dist {aggregate['classical_mean']:.2f} +/- "
        f"{aggregate['classical_sem']:.2f} SEM"
    )
    print(
        f"    ShortestPathPlan   | mean dist {aggregate['planner_mean']:.2f} +/- "
        f"{aggregate['planner_sem']:.2f} SEM"
    )
    print(
        f"    Quantum advantage  | {aggregate['advantage_mean']:+.2f} +/- "
        f"{aggregate['advantage_sem']:.2f} SEM | path closed "
        f"{aggregate['norm_advantage_mean']:+.1f}% +/- {aggregate['norm_advantage_sem']:.1f}% | "
        f"trial wins {aggregate['trial_quantum_wins']}/{aggregate['trial_pairs']} "
        f"({aggregate['trial_quantum_win_rate_mean']:.1%} +/- "
        f"{aggregate['trial_quantum_win_rate_sem']:.1%} SEM, ties {aggregate['trial_ties']}) | "
        f"maze wins {aggregate['maze_quantum_wins']}/{aggregate['n_mazes']}"
    )
    if "per_bin" in aggregate:
        print("\n  Aggregate by detour bin")
        for bin_result in aggregate["per_bin"]:
            upper_bracket = "]" if np.isinf(bin_result["bin_max_detour"]) else ")"
            print(
                f"    {bin_result['bin_label']:<12} | "
                f"[{format_detour_bound(bin_result['bin_min_detour'])}:"
                f"{format_detour_bound(bin_result['bin_max_detour'])}{upper_bracket} | "
                f"n={bin_result['n_mazes']} | detour {bin_result['detour_mean']:.2f}x +/- "
                f"{bin_result['detour_sem']:.2f} SEM | "
                f"advantage {bin_result['advantage_mean']:+.2f} +/- "
                f"{bin_result['advantage_sem']:.2f}"
            )
    return aggregate


def print_summary(results):
    print("\n" + "=" * 88)
    print("  SWEEP SUMMARY")
    print("=" * 88)
    print(
        f"  {'Pair':<10} {'Gap':>4} {'Short':>6} {'Detour':>8} "
        f"{'Quantum':>10} {'Classical':>10} {'Planner':>10} "
        f"{'Adv(SEM)':>14} {'Norm':>14} {'QWin':>15} {'MazeWins':>9}"
    )
    print("  " + "-" * 92)
    for result in results:
        pair = f"{result['maze_dim']}D/{result['latent_dim']}D"
        gap = result["latent_dim"] - result["maze_dim"]
        print(
            f"  {pair:<10} {gap:4d} "
            f"{result['shortest_mean']:6.1f} "
            f"{result['detour_mean']:5.2f}x  "
            f"{result['quantum_mean']:10.2f} "
            f"{result['classical_mean']:10.2f} "
            f"{result['planner_mean']:10.2f} "
            f"{result['advantage_mean']:+6.2f}({result['advantage_sem']:.2f}) "
            f"{result['norm_advantage_mean']:+6.1f}%({result['norm_advantage_sem']:.1f}) "
            f"{result['trial_quantum_win_rate_mean']:6.1%}({result['trial_quantum_win_rate_sem']:.1%}) "
            f"{result['maze_quantum_wins']}/{result['n_mazes']:>2d}"
        )


def build_per_maze_export_rows(results, args, mode_desc, run_id):
    command_line = " ".join(sys.argv)
    rows = []
    for spec_result in results:
        for maze_result in spec_result["per_maze"]:
            rows.append(
                {
                    "run_id": run_id,
                    "command_line": command_line,
                    "spec_mode": mode_desc,
                    "spec_id": spec_result["spec_id"],
                    "selection_mode": spec_result["selection_mode"],
                    "bin_label": maze_result.get("bin_label") or "",
                    "maze_id": f"{spec_result['spec_id']}|seed={maze_result['maze_seed']}",
                    "maze_seed": maze_result["maze_seed"],
                    "candidate_index": (
                        "" if maze_result.get("candidate_index") is None else maze_result["candidate_index"]
                    ),
                    "maze_dim": maze_result["maze_dim"],
                    "latent_dim": maze_result["latent_dim"],
                    "latent_gap": maze_result["latent_dim"] - maze_result["maze_dim"],
                    "side": maze_result["side"],
                    "barriers": maze_result["barriers"],
                    "gaps_per_barrier": maze_result["gaps_per_barrier"],
                    "effective_train_evals": maze_result["effective_train_evals"],
                    "n_runs_eval": args.n_runs,
                    "shortest_path": maze_result["shortest"],
                    "detour_ratio": maze_result["detour_ratio"],
                    "open_fraction": maze_result["open_fraction"],
                    "paired_norm_adv_pct_mean": maze_result["paired"]["normalized_advantage_pct_mean"],
                    "paired_raw_adv_mean": maze_result["paired"]["raw_advantage_mean"],
                    "maze_quantum_win": maze_result["quantum_wins"],
                    "quantum_mean_dist": maze_result["quantum"]["mean_dist"],
                    "classical_mean_dist": maze_result["classical"]["mean_dist"],
                    "planner_mean_dist": maze_result["planner"]["mean_dist"],
                    "paired_quantum_win_rate": maze_result["paired"]["quantum_win_rate"],
                    "paired_n_trials": maze_result["paired"]["n_pairs"],
                }
            )
    return rows


def write_per_maze_export_csv(path, rows):
    if not rows:
        raise ValueError("Cannot export an empty per-maze result set")
    fieldnames = list(rows[0].keys())
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ga-maxiter", type=int, default=None)
    parser.add_argument(
        "--train-evals",
        type=int,
        default=1000,
        help="Approximate fitness-evaluation budget per condition when maxiter is not set.",
    )
    parser.add_argument("--popsize", type=int, default=1)
    parser.add_argument(
        "--de-workers",
        type=int,
        default=1,
        help=(
            "Parallel workers for differential evolution fitness evaluation. "
            "Use 1 for serial or -1 for all cores."
        ),
    )
    parser.add_argument("--n-seeds-ga", type=int, default=4)
    parser.add_argument("--n-runs", type=int, default=100)
    parser.add_argument("--mazes-per-spec", type=int, default=3)
    parser.add_argument(
        "--difficulty-bins",
        type=str,
        default=None,
        help=(
            "Precommit maze selection by detour ratio using label=min:max entries, "
            "for example 'easy=1.00:1.10,mid=1.10:1.30,hard=1.30:inf', or 'default'."
        ),
    )
    parser.add_argument(
        "--mazes-per-bin",
        type=int,
        default=None,
        help=(
            "Accepted mazes per detour bin when --difficulty-bins is active. "
            "Defaults to --mazes-per-spec."
        ),
    )
    parser.add_argument(
        "--bin-max-candidates",
        type=int,
        default=200,
        help="Maximum candidate maze seeds to scan per spec when filling detour bins.",
    )
    parser.add_argument(
        "--plan-bins-only",
        action="store_true",
        help="Print the precommitted bin manifest for each spec, then exit before optimization.",
    )
    parser.add_argument(
        "--per-maze-csv-out",
        type=Path,
        default=None,
        help="Optional path to export one CSV row per maze/spec result.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional run identifier to include in per-maze exports.",
    )
    parser.add_argument(
        "--maze-dims",
        type=str,
        default=None,
        help="Comma-separated maze dimensions to include, e.g. 2,3",
    )
    parser.add_argument(
        "--latent-dims",
        type=str,
        default=None,
        help="Absolute latent dims to sweep for each maze dim, e.g. 2,4,6,8",
    )
    parser.add_argument(
        "--latent-offsets",
        type=str,
        default=None,
        help="Offsets added to maze dim to get latent dim, e.g. 0,2,4,6",
    )
    parser.add_argument(
        "--side-override",
        type=int,
        default=None,
        help="Override maze side length for all selected specs.",
    )
    parser.add_argument(
        "--barriers-override",
        type=int,
        default=None,
        help="Override number of barrier hyperplanes for all selected specs.",
    )
    parser.add_argument(
        "--gaps-override",
        type=int,
        default=None,
        help="Override number of random gaps per barrier for all selected specs.",
    )
    args = parser.parse_args()
    try:
        args.difficulty_bins_parsed = parse_difficulty_bins(args.difficulty_bins)
        if args.mazes_per_spec < 1:
            raise ValueError("--mazes-per-spec must be >= 1")
        if args.mazes_per_bin is not None and args.mazes_per_bin < 1:
            raise ValueError("--mazes-per-bin must be >= 1")
        if args.bin_max_candidates < 1:
            raise ValueError("--bin-max-candidates must be >= 1")
        if args.de_workers == 0 or args.de_workers < -1:
            raise ValueError("--de-workers must be 1, -1, or a positive integer")
        if args.plan_bins_only and not args.difficulty_bins_parsed:
            raise ValueError("--plan-bins-only requires --difficulty-bins")
    except ValueError as exc:
        parser.error(str(exc))
    specs, mode_desc = build_specs(args)

    print("=" * 88)
    print("  HIGHER-DIMENSIONAL MAZE SCALING SWEEP")
    print("  Quantum+Adaptive vs Classical+Adaptive vs ShortestPathPlanner")
    print("=" * 88)
    if args.ga_maxiter is None:
        budget_desc = f"train-evals~{args.train_evals}"
    else:
        budget_desc = f"maxiter={args.ga_maxiter}"
    print(
        f"  Optimizer: differential evolution | {budget_desc} | popsize={args.popsize} | "
        f"DE workers={args.de_workers} | "
        f"GA seeds={args.n_seeds_ga} | eval runs={args.n_runs} | mazes/spec={args.mazes_per_spec}"
    )
    print(f"  Spec mode: {mode_desc}")
    if args.difficulty_bins_parsed:
        bin_desc = ", ".join(format_difficulty_bin(bin_spec) for bin_spec in args.difficulty_bins_parsed)
        print(
            f"  Difficulty bins: {bin_desc} | "
            f"mazes/bin={active_mazes_per_bin(args)} | "
            f"candidate cap/spec={args.bin_max_candidates}"
        )
        if args.plan_bins_only:
            print("  Manifest mode: planning only (no controller optimization)")
    print("  Eval seeds: paired quantum/classical trajectories per maze")

    results = [run_spec(spec, args) for spec in specs]
    if args.plan_bins_only:
        print("\n" + "=" * 88)
        print("  BIN MANIFESTS LOCKED")
        print("=" * 88)
        print("  Precommitted difficulty-bin manifests were printed above.")
        print("  No controller optimization was run.")
        return
    if args.per_maze_csv_out is not None:
        run_id = args.run_id or f"maze-scaling-{int(time.time())}"
        export_rows = build_per_maze_export_rows(results, args, mode_desc, run_id)
        write_per_maze_export_csv(args.per_maze_csv_out, export_rows)
        print(f"  Per-maze export CSV: {args.per_maze_csv_out}")
    print_summary(results)


if __name__ == "__main__":
    main()
