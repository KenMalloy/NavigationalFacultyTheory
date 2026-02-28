"""
Maze Navigation via Higher-Dimensional Quantum Feedback
=======================================================

A 6D quantum agent solves a 2D maze using only evolution + radical pair
spin dynamics. No pathfinding algorithm, no map, no planning.

The agent's internal state is a 6D conformational vector (the "brain").
Its 2D position is projected from this higher-dimensional state.
At each step, a radical pair event updates the internal state,
and the internal state determines the move direction.

The GA evolves only the feedback parameters. The quantum feedback loop
discovers the navigation strategy.

Demonstrates: higher-dimensional quantum navigation solving a
lower-dimensional spatial problem — the core NFT claim.
"""

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import differential_evolution
import time

# ── Physical constants ────────────────────────────────────────────────────
MU_B = 9.274_010_0783e-24
HBAR = 1.054_571_817e-34
G_E = 2.002_319_304

# ── Spin operators (12-dim) ───────────────────────────────────────────────

def build_operators():
    sx = np.array([[0, 1], [1, 0]], dtype=complex) / 2
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex) / 2
    sz = np.array([[1, 0], [0, -1]], dtype=complex) / 2
    I2 = np.eye(2, dtype=complex)
    sq2 = np.sqrt(2.0)
    ix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / sq2
    iy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / sq2
    iz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
    I3 = np.eye(3, dtype=complex)

    def k3(A, B, C):
        return np.kron(np.kron(A, B), C)

    ops = {
        'S1x': k3(sx, I2, I3), 'S1y': k3(sy, I2, I3), 'S1z': k3(sz, I2, I3),
        'S2x': k3(I2, sx, I3), 'S2y': k3(I2, sy, I3), 'S2z': k3(I2, sz, I3),
        'INx': k3(I2, I2, ix), 'INy': k3(I2, I2, iy), 'INz': k3(I2, I2, iz),
        'I12': np.eye(12, dtype=complex),
    }
    S1S2 = ops['S1x'] @ ops['S2x'] + ops['S1y'] @ ops['S2y'] + ops['S1z'] @ ops['S2z']
    ops['P_S'] = 0.25 * ops['I12'] - S1S2
    return ops


def build_H(ops, B, a_MHz, J_MHz, phi):
    w = G_E * MU_B * B / HBAR * 1e-6
    a = 2 * np.pi * a_MHz
    J = 2 * np.pi * J_MHz
    cp, sp = np.cos(phi), np.sin(phi)
    H = w * (cp * (ops['S1z'] + ops['S2z']) + sp * (ops['S1x'] + ops['S2x']))
    H += a * (ops['S1x'] @ ops['INx'] + ops['S1y'] @ ops['INy'] + ops['S1z'] @ ops['INz'])
    H += J * (ops['S1x'] @ ops['S2x'] + ops['S1y'] @ ops['S2y'] + ops['S1z'] @ ops['S2z'])
    return H


def compute_PS(H, P_S, tau=1.0):
    eigvals, eigvecs = eigh(H)
    U = eigvecs @ np.diag(np.exp(-1j * eigvals * tau)) @ eigvecs.conj().T
    rho0 = P_S / np.trace(P_S).real
    rho_t = U @ rho0 @ U.conj().T
    return float(np.clip(np.trace(P_S @ rho_t).real, 0.01, 0.99))


# ── Maze definition ──────────────────────────────────────────────────────

def make_maze(size=8, difficulty="easy"):
    """Create a maze. 0=open, 1=wall. Start=(0,0), Goal=(size-1,size-1)."""
    m = np.zeros((size, size), dtype=int)

    if difficulty == "easy":
        m[1, 1:6] = 1
        m[3, 2:7] = 1
        m[5, 0:5] = 1
        m[2, 3] = 1
        m[4, 1] = 1
        m[6, 3:6] = 1

    elif difficulty == "hard":
        # Serpentine with weaving bumps.
        # Key insight: bumps can ONLY go in two-row bands (rows 0-1) where
        # there's space to bypass. Single-row corridors between spanning walls
        # (rows 3, 5) must stay fully open or the maze becomes unsolvable.
        #
        # Spanning walls force 3 direction reversals:
        m[2, 0:7] = 1    # row 2: gap at col 7 (go right)
        m[4, 1:8] = 1    # row 4: gap at col 0 (go left)
        m[6, 0:7] = 1    # row 6: gap at col 7 (go right)
        # Bumps in rows 0-1 (two-row band — can weave between them):
        m[0, 2] = 1      # forces dip to row 1
        m[1, 4] = 1      # forces back to row 0
        m[0, 6] = 1      # forces dip to row 1 again
        # Rows 3 and 5 are single-row corridors — no bumps allowed
        # Bumps in row 7 (distractors, don't block goal path since goal=(7,7)):
        m[7, 2] = 1
        m[7, 4] = 1

    elif difficulty == "multipath":
        # 3 walls × 2 gaps each = 8 possible routes.
        # The optimal route zigzags: left gap → right gap → right gap.
        # Route lengths (BFS verified):
        #   (1,2)→(3,5)→(5,7) = 14  ← OPTIMAL (Manhattan-optimal, no backtracking)
        #   (1,2)→(3,1)→(5,3) = 16
        #   (1,2)→(3,1)→(5,7) = 16
        #   (1,6)→(3,5)→(5,7) = 16
        #   (1,2)→(3,5)→(5,3) = 18
        #   (1,6)→(3,5)→(5,3) = 20
        #   (1,6)→(3,1)→(5,3) = 24  (worst)
        #   (1,6)→(3,1)→(5,7) = 24  (worst)
        # Row 1: gaps at cols 2 and 6
        m[1, 0:2] = 1     # cols 0-1
        m[1, 3:6] = 1     # cols 3-5
        m[1, 7] = 1       # col 7
        # Row 3: gaps at cols 1 and 5
        m[3, 0] = 1       # col 0
        m[3, 2:5] = 1     # cols 2-4
        m[3, 6:8] = 1     # cols 6-7
        # Row 5: gaps at cols 3 and 7
        m[5, 0:3] = 1     # cols 0-2
        m[5, 4:7] = 1     # cols 4-6

    elif difficulty == "fourway":
        # Vertical barrier forces ALL 4 movement directions.
        # Left zone (col 0) → bottom connector → UP corridor (col 2) →
        # crossing at row 2 → right across → down → LEFT traverse → down → goal.
        # BFS optimal: 26 steps using DOWN(10), RIGHT(10), UP(3), LEFT(3).
        m[0, 1:4] = 1     # row 0: wall cols 1-3
        m[1, 1:4] = 1     # row 1: wall cols 1-3
        m[2, 1] = 1       # row 2: wall col 1 (crossing: cols 2-7 open)
        m[3, 1] = 1       # row 3: wall col 1
        m[3, 3:7] = 1     # row 3: wall cols 3-6 (gap at col 7)
        m[4, 1] = 1       # row 4: wall col 1
        m[4, 3] = 1       # row 4: wall col 3
        m[5, 3] = 1       # row 5: wall col 3
        m[5, 5:8] = 1     # row 5: wall cols 5-7
        m[6, 3] = 1       # row 6: wall col 3
        m[7, 3] = 1       # row 7: wall col 3

    elif difficulty == "serpentine":
        # True serpentine — only ONE valid path, must reverse direction 4 times.
        # Size must be 10 for this layout.
        size = 10
        m = np.zeros((size, size), dtype=int)
        # Row 2: wall with gap on right
        m[2, 0:9] = 1
        # Row 4: wall with gap on left
        m[4, 1:10] = 1
        # Row 6: wall with gap on right
        m[6, 0:9] = 1
        # Row 8: wall with gap on left
        m[8, 1:10] = 1

    m[0, 0] = 0
    m[size - 1, size - 1] = 0
    return m


MOVES = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])  # right, left, down, up
MOVE_NAMES = ("Right", "Left", "Down", "Up")


def verify_solvable(maze):
    """BFS from (0,0) to (size-1, size-1). Returns shortest path length or -1."""
    dist_map = bfs_distance_map(maze)
    return dist_map[0, 0]


def bfs_distance_map(maze):
    """BFS distance from every open cell to the goal. -1 for walls/unreachable."""
    from collections import deque
    size = maze.shape[0]
    goal = (size - 1, size - 1)
    dist_map = np.full((size, size), -1, dtype=int)
    if maze[goal]:
        return dist_map
    dist_map[goal] = 0
    queue = deque([goal])
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and dist_map[nr, nc] == -1 and maze[nr, nc] == 0:
                dist_map[nr, nc] = dist_map[r, c] + 1
                queue.append((nr, nc))
    return dist_map


def choose_bfs_move(x, y, maze, dist_map):
    """Choose the valid neighbor with smallest BFS distance to the goal."""
    best_move = None
    best_dist = None
    for idx, (dx, dy) in enumerate(MOVES):
        nx, ny = x + dx, y + dy
        if 0 <= nx < maze.shape[0] and 0 <= ny < maze.shape[1] and maze[nx, ny] == 0:
            cand_dist = dist_map[nx, ny]
            if cand_dist < 0:
                continue
            if best_dist is None or cand_dist < best_dist:
                best_dist = cand_dist
                best_move = (idx, nx, ny)
    return best_move


def run_shortest_path_baseline(maze, dist_map):
    """Deterministic shortest-path baseline using the full maze map."""
    size = maze.shape[0]
    goal = (size - 1, size - 1)
    x, y = 0, 0
    positions = [(x, y)]
    max_steps = size * size * 4

    for _ in range(max_steps):
        if (x, y) == goal:
            break
        best_move = choose_bfs_move(x, y, maze, dist_map)
        if best_move is None:
            break
        _, x, y = best_move
        positions.append((x, y))

    reached_goal = (x, y) == goal
    final_dist = dist_map[x, y]
    return final_dist, len(positions) - 1, reached_goal, positions


def run_wall_follower(maze, n_steps, hand="right"):
    """Classical local heuristic baseline with no global map."""
    size = maze.shape[0]
    goal = (size - 1, size - 1)
    x, y = 0, 0
    # Start facing right.
    heading = 0
    positions = [(x, y)]
    hand_delta = 1 if hand == "right" else -1

    for _ in range(n_steps):
        if (x, y) == goal:
            break

        candidate_order = [
            (heading + hand_delta) % 4,      # turn toward the wall hand
            heading,                         # go straight
            (heading - hand_delta) % 4,      # turn away from the wall hand
            (heading + 2) % 4,               # turn around
        ]
        moved = False
        for idx in candidate_order:
            nx, ny = x + MOVES[idx, 0], y + MOVES[idx, 1]
            if 0 <= nx < size and 0 <= ny < size and maze[nx, ny] == 0:
                x, y = nx, ny
                heading = idx
                positions.append((x, y))
                moved = True
                break
        if not moved:
            break

    reached_goal = (x, y) == goal
    return abs(x - goal[0]) + abs(y - goal[1]), len(positions) - 1, reached_goal, positions


def summarize_trials(trials):
    dists = [trial[0] for trial in trials]
    path_lengths = [trial[1] for trial in trials if trial[2]]
    goals_reached = sum(1 for trial in trials if trial[2])
    return {
        'mean_dist': float(np.mean(dists)),
        'std': float(np.std(dists)),
        'goal_rate': goals_reached / len(trials),
        'min_dist': int(np.min(dists)),
        'mean_path': float(np.mean(path_lengths)) if path_lengths else float('inf'),
        'min_path': int(min(path_lengths)) if path_lengths else float('inf'),
        'n_trials': len(trials),
    }


# ── Precompute P_S gradient w.r.t. extended state ─────────────────────────

def compute_gradient(ops, B, a_base, J_base, alpha, beta, gamma_mod, tau=1.0):
    """Gradient of P_S w.r.t. 8D state [theta(6), x, y]."""
    P_S = ops['P_S']

    def ps_at(state):
        # state = [theta0..5, x, y]
        a_N = a_base + alpha * state[0] + 0.5 * state[6]  # x position modulates hyperfine
        J = J_base + beta * state[1] + 0.3 * state[7]     # y position modulates exchange
        phi = gamma_mod * state[2]
        H = build_H(ops, B, a_N, J, phi)
        return compute_PS(H, P_S, tau)

    state0 = np.zeros(8)
    ps0 = ps_at(state0)
    grad = np.zeros(8)
    eps = 0.01
    for i in range(8):
        sp = state0.copy()
        sp[i] = eps
        sm = state0.copy()
        sm[i] = -eps
        grad[i] = (ps_at(sp) - ps_at(sm)) / (2 * eps)

    return ps0, grad


# ── Fast simulation ──────────────────────────────────────────────────────

def run_maze(rng, maze, n_steps, ps0, grad, delta_S, delta_T,
             move_weights, use_adaptive, use_quantum, dist_map=None):
    """Navigate the maze using radical pair feedback.

    move_weights: (4, 8) matrix mapping [theta(6), x_norm, y_norm] to move preferences.
    The agent chooses the move direction with the highest weight·state value
    among valid (non-wall) moves.

    Returns: bfs_distance, path_length, reached_goal, positions.
    """
    size = maze.shape[0]
    theta = np.zeros(6)
    x, y = 0, 0
    goal = (size - 1, size - 1)
    positions = [(x, y)]
    reached_goal = False

    for step in range(n_steps):
        if (x, y) == goal:
            reached_goal = True
            break

        # Extended state for P_S computation
        pos_scale = max(size - 1, 1)
        state = np.concatenate([theta, [x / pos_scale, y / pos_scale]])

        # Radical pair event
        if use_quantum:
            if use_adaptive:
                ps = ps0 + np.dot(grad, state)
                ps = np.clip(ps, 0.01, 0.99)
            else:
                ps = ps0
        else:
            ps = 0.5

        is_singlet = rng.random() < ps
        if is_singlet:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

        # Determine move from theta + position via move_weights
        full_state = np.concatenate([theta, [x / (size - 1), y / (size - 1)]])
        scores = move_weights @ full_state  # (4,) scores for each direction
        # Sort moves by score, pick best valid one
        order = np.argsort(-scores)
        for idx in order:
            nx, ny = x + MOVES[idx, 0], y + MOVES[idx, 1]
            if 0 <= nx < size and 0 <= ny < size and maze[nx, ny] == 0:
                x, y = nx, ny
                if (x, y) == goal:
                    reached_goal = True
                break

        positions.append((x, y))
        if reached_goal:
            break

    # Use BFS distance if available, otherwise Manhattan
    if dist_map is not None:
        final_dist = dist_map[x, y]
    else:
        final_dist = abs(x - goal[0]) + abs(y - goal[1])
    return final_dist, len(positions) - 1, reached_goal, positions


# ── GA fitness ────────────────────────────────────────────────────────────

def fitness_fn(params, ops, B, a_base, J_base, maze, n_steps, n_seeds, base_seed,
               dist_map, use_adaptive=True, use_quantum=True):
    """Evaluate: mean BFS distance to goal."""
    delta_S = params[:6]
    delta_T = params[6:12]
    alpha = params[12]
    beta = params[13]
    gamma_mod = params[14]
    move_weights = params[15:47].reshape(4, 8)  # 4 directions × (6 theta + 2 position)

    ps0, grad = compute_gradient(ops, B, a_base, J_base, alpha, beta, gamma_mod)

    total_dist = 0
    for s in range(n_seeds):
        rng = np.random.default_rng(base_seed + s)
        dist, _, _, _ = run_maze(rng, maze, n_steps, ps0, grad,
                                  delta_S, delta_T, move_weights, use_adaptive,
                                  use_quantum,
                                  dist_map)
        total_dist += dist
    return total_dist / n_seeds


def evaluate_agent_condition(config, maze, n_steps, n_runs, dist_map, base_seed=2000):
    """Evaluate a learned/tuned controller across multiple seeds."""
    dS, dT, p0, g, mw, adaptive, quantum = config
    trials = []
    for s in range(n_runs):
        rng = np.random.default_rng(base_seed + s)
        trials.append(
            run_maze(rng, maze, n_steps, p0, g, dS, dT, mw, adaptive, quantum, dist_map)
        )
    return summarize_trials(trials)


def evolve_controller(label, bounds, ops, B, a_base, J_base, maze, n_steps, n_seeds_ga,
                      dist_map, maxiter, use_adaptive, use_quantum):
    """Independently optimize a controller for a specific dynamical regime."""
    print(f"\n  Re-optimizing {label} baseline ({'adaptive' if use_adaptive else 'fixed'} / "
          f"{'quantum' if use_quantum else 'classical'})")
    t0 = time.time()
    result = differential_evolution(
        fitness_fn,
        bounds=bounds,
        args=(ops, B, a_base, J_base, maze, n_steps, n_seeds_ga, 1500,
              dist_map, use_adaptive, use_quantum),
        maxiter=maxiter,
        popsize=10,
        seed=84 if use_quantum else 126,
        tol=1e-6,
        polish=False,
    )
    print(f"    done in {time.time() - t0:.1f}s | best mean dist = {result.fun:.2f}/{dist_map[0, 0]}")

    best = result.x
    delta_S = best[:6]
    delta_T = best[6:12]
    alpha, beta, gamma_mod = best[12], best[13], best[14]
    move_weights = best[15:47].reshape(4, 8)
    ps0, grad = compute_gradient(ops, B, a_base, J_base, alpha, beta, gamma_mod)
    return delta_S, delta_T, ps0, grad, move_weights, use_adaptive, use_quantum


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  MAZE NAVIGATION VIA HIGHER-DIMENSIONAL QUANTUM FEEDBACK")
    print("  6D quantum agent solves 2D maze using only evolution")
    print("=" * 72)

    B = 50e-6
    a_base = 10.0
    J_base = 0.0
    n_seeds_ga = 8
    n_runs = 100

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--difficulty", choices=["easy", "hard", "multipath", "fourway", "serpentine"], default="hard")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--ga-maxiter", type=int, default=40)
    parser.add_argument("--control-ga-maxiter", type=int, default=20)
    parser.add_argument("--optimize-controls", action="store_true",
                        help="Independently optimize fixed-basis and classical controls.")
    args = parser.parse_args()

    n_steps = args.steps
    ops = build_operators()
    maze_size = 10 if args.difficulty == "serpentine" else 8  # fourway uses 8
    maze = make_maze(maze_size, args.difficulty)

    dist_map = bfs_distance_map(maze)
    shortest = dist_map[0, 0]
    if shortest < 0:
        print("\n  ERROR: maze is not solvable! Aborting.")
        return
    print(f"\n  Maze verified solvable (BFS shortest path: {shortest} steps)")

    print("\n  Maze (0=open, 1=wall):")
    for row in maze:
        print("  " + " ".join("█" if c else "·" for c in row))
    goal_r, goal_c = maze_size - 1, maze_size - 1
    print(f"  Start: (0,0)  Goal: ({goal_r},{goal_c})")
    print(f"  Difficulty: {args.difficulty}")
    print(f"  BFS distance: {shortest}")
    print(f"  Steps per trial: {n_steps}")

    # GA bounds: 15 feedback params + 32 move-weight params = 47
    bounds = (
        [(-0.2, 0.2)] * 6 +     # delta_S
        [(-0.2, 0.2)] * 6 +     # delta_T
        [(0.0, 5.0)] +          # alpha
        [(0.0, 3.0)] +          # beta
        [(0.0, 0.5)] +          # gamma
        [(-1.0, 1.0)] * 32      # move_weights (4×8: 4 dirs × (6 theta + 2 pos))
    )

    print(f"\n  GA: {47} parameters (15 feedback + 32 move-weights)")
    print(f"  Seeds per eval: {n_seeds_ga}")

    # ── Evolution ─────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  EVOLVING NAVIGATION STRATEGY")
    print("=" * 72)

    gen = [0]
    t0 = time.time()

    def callback(xk, convergence=0):
        gen[0] += 1
        d = fitness_fn(xk, ops, B, a_base, J_base, maze, n_steps, n_seeds_ga, 500,
                       dist_map, True, True)
        print(f"  Gen {gen[0]:3d} | mean_dist = {d:.2f}/{shortest} | "
              f"elapsed = {time.time() - t0:.1f}s", flush=True)

    result = differential_evolution(
        fitness_fn,
        bounds=bounds,
        args=(ops, B, a_base, J_base, maze, n_steps, n_seeds_ga, 500, dist_map, True, True),
        maxiter=args.ga_maxiter,
        popsize=10,
        seed=42,
        callback=callback,
        tol=1e-6,
    )

    elapsed = time.time() - t0
    print(f"\n  GA completed in {elapsed:.1f}s")
    print(f"  Best mean distance: {result.fun:.2f}/{shortest}")

    best = result.x
    delta_S = best[:6]
    delta_T = best[6:12]
    alpha, beta, gamma_mod = best[12], best[13], best[14]
    move_weights = best[15:47].reshape(4, 8)  # 4 directions × (6 theta + 2 position)

    ps0, grad = compute_gradient(ops, B, a_base, J_base, alpha, beta, gamma_mod)

    # ── Comparison ────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  FOUR-WAY COMPARISON")
    print("=" * 72)

    # Random feedback for control
    rng_r = np.random.default_rng(99)
    delta_S_r = rng_r.uniform(-0.2, 0.2, 6)
    delta_T_r = rng_r.uniform(-0.2, 0.2, 6)
    mw_r = rng_r.uniform(-1, 1, (4, 8))
    ps0_r, grad_r = compute_gradient(ops, B, a_base, J_base,
                                      rng_r.uniform(0, 5), rng_r.uniform(0, 3),
                                      rng_r.uniform(0, 0.5))

    conditions = {
        "Quantum+Evolved": (delta_S, delta_T, ps0, grad, move_weights, True, True),
        "FixedBasis+QuantumTuned": (delta_S, delta_T, ps0, grad, move_weights, False, True),
        "Classical+QuantumTuned": (delta_S, delta_T, ps0, grad, move_weights, True, False),
        "Quantum+Random": (delta_S_r, delta_T_r, ps0_r, grad_r, mw_r, True, True),
    }

    if args.optimize_controls:
        conditions["FixedBasis+Reoptimized"] = evolve_controller(
            "FixedBasis", bounds, ops, B, a_base, J_base, maze, n_steps,
            n_seeds_ga, dist_map, args.control_ga_maxiter, False, True
        )
        conditions["Classical+Reoptimized"] = evolve_controller(
            "Classical", bounds, ops, B, a_base, J_base, maze, n_steps,
            n_seeds_ga, dist_map, args.control_ga_maxiter, True, False
        )

    results = {}
    for name, config in conditions.items():
        results[name] = evaluate_agent_condition(config, maze, n_steps, n_runs, dist_map)

    results["ShortestPathPlanner"] = summarize_trials(
        [run_shortest_path_baseline(maze, dist_map)]
    )
    results["RightWallFollower"] = summarize_trials(
        [run_wall_follower(maze, n_steps, hand="right")]
    )
    results["LeftWallFollower"] = summarize_trials(
        [run_wall_follower(maze, n_steps, hand="left")]
    )

    print(f"\n  {'Condition':<28} {'Mean dist':>10} {'Goal rate':>10} "
          f"{'Avg path':>10} {'Best path':>10}")
    print(f"  {'-' * 70}")
    for name, r in results.items():
        avg_p = f"{r['mean_path']:.1f}" if r['goal_rate'] > 0 else "—"
        best_p = f"{r['min_path']}" if r['goal_rate'] > 0 else "—"
        print(f"  {name:<28} {r['mean_dist']:10.2f} {r['goal_rate']:10.1%} "
              f"{avg_p:>10} {best_p:>10}")
    print(f"\n  BFS optimal path length: {shortest}")

    # ── Example path ──────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  EXAMPLE PATH (Quantum+Evolved, seed=0)")
    print("=" * 72)

    rng = np.random.default_rng(2000)
    dist, steps, reached, positions = run_maze(
        rng, maze, n_steps, ps0, grad, delta_S, delta_T, move_weights, True, True,
        dist_map)

    path_grid = np.full((maze_size, maze_size), "·")
    for r in range(maze_size):
        for c in range(maze_size):
            if maze[r, c]:
                path_grid[r, c] = "█"
    for i, (px, py) in enumerate(positions):
        if path_grid[px, py] not in ("█", "S", "G"):
            path_grid[px, py] = "○"
    path_grid[0, 0] = "S"
    path_grid[goal_r, goal_c] = "G"

    print()
    for row in path_grid:
        print("  " + " ".join(row))
    print(f"\n  Steps: {steps}, Final dist: {dist}, Reached goal: {reached}")

    # ── Verdict ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  INTERPRETATION")
    print("=" * 72)

    qe = results["Quantum+Evolved"]
    fe = results["FixedBasis+QuantumTuned"]
    ce = results["Classical+QuantumTuned"]
    qr = results["Quantum+Random"]
    sp = results["ShortestPathPlanner"]
    rw = results["RightWallFollower"]
    lw = results["LeftWallFollower"]

    print("\n  Baseline framing:")
    print("    Quantum+Evolved is the learned NFT controller.")
    print("    *+QuantumTuned controls reuse parameters optimized for the quantum controller.")
    if args.optimize_controls:
        print("    *+Reoptimized controls were evolved independently in their own regimes.")
    print("    ShortestPathPlanner is a competent classical upper bound with full maze knowledge.")
    print("    WallFollower baselines are local classical heuristics with no global map.")

    print("\n  Takeaways:")
    if qe['mean_dist'] < fe['mean_dist'] and qe['mean_dist'] < ce['mean_dist']:
        print("    Quantum+Evolved beats the same-architecture controls that inherit quantum-tuned parameters.")
    else:
        print("    Quantum+Evolved does not cleanly beat the same-architecture inherited controls.")

    if args.optimize_controls:
        cre = results["Classical+Reoptimized"]
        fre = results["FixedBasis+Reoptimized"]
        if qe['mean_dist'] < cre['mean_dist'] and qe['mean_dist'] < fre['mean_dist']:
            print("    Quantum+Evolved also beats independently re-optimized learned controls.")
        else:
            print("    Independently re-optimized learned controls narrow or erase the quantum gap.")

    if sp['goal_rate'] >= qe['goal_rate'] and sp['mean_dist'] <= qe['mean_dist']:
        print("    A competent classical planner solves this benchmark at least as well as the quantum controller.")
    else:
        print("    The quantum controller remains competitive even against the shortest-path planner.")

    if qe['goal_rate'] > max(rw['goal_rate'], lw['goal_rate']):
        print("    Quantum+Evolved beats simple map-free classical heuristics on this maze.")
    else:
        print("    Simple map-free classical heuristics match or beat the quantum controller here.")

    print("\n  Honest reading:")
    print("    This benchmark is best read as a proof-of-principle for the learned quantum feedback")
    print("    controller, not as a general claim that quantum navigation beats the best classical")
    print("    algorithms on maze solving.")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
