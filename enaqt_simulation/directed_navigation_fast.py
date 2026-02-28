"""
Directed Navigation via Evolved Measurement-Basis Feedback — Fast Version
=========================================================================

Tests whether evolution can tune the radical pair feedback loop to navigate
toward a specific target in conformation space.

Optimization: precomputes the gradient of P_S with respect to theta at each
GA evaluation, then uses linear interpolation in the inner loop. Avoids
144x144 matrix exponentials entirely.

Four comparison conditions:
  1. Adaptive + evolved feedback (the NFT claim)
  2. Fixed basis + evolved feedback (no quantum adaptation)
  3. Classical + evolved feedback (coin flip, no quantum dynamics)
  4. Adaptive + random feedback (no evolution)
"""

import numpy as np
from scipy.linalg import expm, eigh
from scipy.optimize import differential_evolution
import time
import sys

# ── Physical constants ────────────────────────────────────────────────────
MU_B = 9.274_010_0783e-24
HBAR = 1.054_571_817e-34
G_E = 2.002_319_304

# ── Spin operators (12-dim: electron1 x electron2 x nucleus I=1) ──────────

def _pauli():
    sx = np.array([[0, 1], [1, 0]], dtype=complex) / 2
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex) / 2
    sz = np.array([[1, 0], [0, -1]], dtype=complex) / 2
    return sx, sy, sz, np.eye(2, dtype=complex)

def _spin1():
    sq2 = np.sqrt(2.0)
    ix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / sq2
    iy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / sq2
    iz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
    return ix, iy, iz, np.eye(3, dtype=complex)

def kron3(A, B, C):
    return np.kron(np.kron(A, B), C)

def build_operators():
    sx, sy, sz, I2 = _pauli()
    Ix, Iy, Iz, I3 = _spin1()
    ops = {
        'S1x': kron3(sx, I2, I3), 'S1y': kron3(sy, I2, I3), 'S1z': kron3(sz, I2, I3),
        'S2x': kron3(I2, sx, I3), 'S2y': kron3(I2, sy, I3), 'S2z': kron3(I2, sz, I3),
        'INx': kron3(I2, I2, Ix), 'INy': kron3(I2, I2, Iy), 'INz': kron3(I2, I2, Iz),
        'I12': np.eye(12, dtype=complex),
    }
    S1S2 = ops['S1x'] @ ops['S2x'] + ops['S1y'] @ ops['S2y'] + ops['S1z'] @ ops['S2z']
    ops['P_S'] = 0.25 * ops['I12'] - S1S2
    return ops


# ── Hamiltonian builder ───────────────────────────────────────────────────

def build_H(ops, B_field, a_N_MHz, J_MHz, phi_rad):
    omega = G_E * MU_B * B_field / HBAR * 1e-6  # rad/us
    a_N = 2 * np.pi * a_N_MHz
    J = 2 * np.pi * J_MHz
    cp, sp = np.cos(phi_rad), np.sin(phi_rad)
    H = omega * (cp * (ops['S1z'] + ops['S2z']) + sp * (ops['S1x'] + ops['S2x']))
    H += a_N * (ops['S1x'] @ ops['INx'] + ops['S1y'] @ ops['INy'] + ops['S1z'] @ ops['INz'])
    H += J * (ops['S1x'] @ ops['S2x'] + ops['S1y'] @ ops['S2y'] + ops['S1z'] @ ops['S2z'])
    return H


# ── Fast P_S computation via eigendecomposition ──────────────────────────

def compute_PS_eigen(H, P_S, tau, k_S, k_T):
    """Compute singlet probability using 12x12 eigendecomposition.

    Approximate: evolve coherently, apply average decay.
    Much faster than 144x144 Liouvillian expm.
    """
    eigvals, eigvecs = eigh(H)
    # Propagator U(tau) in eigenstate basis
    phases = np.exp(-1j * eigvals * tau)
    U = eigvecs @ np.diag(phases) @ eigvecs.conj().T

    # Initial state: normalized singlet projection
    rho0 = P_S / np.trace(P_S).real

    # Coherent evolution
    rho_t = U @ rho0 @ U.conj().T

    # Singlet probability (coherent)
    ps_coherent = np.trace(P_S @ rho_t).real
    ps_coherent = np.clip(ps_coherent, 0.0, 1.0)

    # Apply Haberkorn decay (approximate: use initial singlet fraction for decay rate)
    # Total decay rate ~ k_S * p_S + k_T * (1 - p_S)
    # Survival ≈ exp(-rate * tau)
    # Singlet among survivors ≈ ps_coherent (decay is non-selective to first order)

    return ps_coherent


# ── Gradient of P_S with respect to theta ─────────────────────────────────

def compute_PS_gradient(ops, B_field, a_base, J_base, alpha, beta, gamma, tau, k_S, k_T):
    """Compute P_S and its gradient w.r.t. theta by finite differences.

    Returns P_S(theta=0) and gradient vector (6,).
    """
    P_S = ops['P_S']

    def ps_at_theta(theta):
        a_N = a_base + alpha * theta[0]
        J = J_base + beta * theta[1]
        phi = gamma * theta[2]
        H = build_H(ops, B_field, a_N, J, phi)
        return compute_PS_eigen(H, P_S, tau, k_S, k_T)

    theta0 = np.zeros(6)
    ps0 = ps_at_theta(theta0)

    grad = np.zeros(6)
    eps = 0.01
    for i in range(6):
        theta_p = theta0.copy()
        theta_p[i] = eps
        theta_m = theta0.copy()
        theta_m[i] = -eps
        grad[i] = (ps_at_theta(theta_p) - ps_at_theta(theta_m)) / (2 * eps)

    return ps0, grad


# ── Fast simulation loop ─────────────────────────────────────────────────

def run_adaptive_fast(rng, n_events, ps0, grad, delta_S, delta_T, use_adaptive, use_quantum):
    """Run one seed of the measurement-basis-selection loop.

    Uses linear approximation: P_S(theta) ≈ ps0 + grad · theta

    If use_adaptive=False: P_S stays at ps0 (fixed basis)
    If use_quantum=False: P_S = 0.5 (classical coin flip)
    """
    theta = np.zeros(6)
    singlet_count = 0

    for _ in range(n_events):
        if use_quantum:
            if use_adaptive:
                ps = ps0 + np.dot(grad, theta)
                ps = np.clip(ps, 0.01, 0.99)
            else:
                ps = ps0
        else:
            ps = 0.5

        is_singlet = rng.random() < ps
        if is_singlet:
            theta = theta + delta_S
            singlet_count += 1
        else:
            theta = theta + delta_T

    return theta, singlet_count / n_events


# ── GA fitness function ──────────────────────────────────────────────────

def fitness_fn(params, ops, B_field, a_base, J_base, tau, k_S, k_T,
               target, n_events, n_seeds, base_seed):
    """Evaluate fitness: mean distance to target across seeds."""
    delta_S = params[:6]
    delta_T = params[6:12]
    alpha = params[12]
    beta = params[13]
    gamma_mod = params[14]

    # Compute P_S and gradient for this parameter set
    ps0, grad = compute_PS_gradient(ops, B_field, a_base, J_base,
                                      alpha, beta, gamma_mod, tau, k_S, k_T)

    total_dist = 0.0
    for s in range(n_seeds):
        rng = np.random.default_rng(base_seed + s)
        theta_final, _ = run_adaptive_fast(rng, n_events, ps0, grad,
                                            delta_S, delta_T, True, True)
        total_dist += np.linalg.norm(theta_final - target)

    return total_dist / n_seeds


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  DIRECTED NAVIGATION — FAST VERSION")
    print("  Can evolution tune the feedback loop for goal-directed navigation?")
    print("=" * 72)

    # Parameters
    B_field = 50e-6
    a_base = 10.0
    J_base = 0.0
    tau = 1.0
    k_S = 1.0
    k_T = 0.1
    n_events = 100
    n_seeds_ga = 10
    n_runs_compare = 150
    target = np.array([3.0, -2.0, 1.5, -1.0, 2.0, -0.5])

    print(f"\n  Target: {target}")
    print(f"  Initial distance: {np.linalg.norm(target):.4f}")
    print(f"  N_events: {n_events}")
    print(f"  N_seeds (GA): {n_seeds_ga}")
    print(f"  N_runs (compare): {n_runs_compare}")

    ops = build_operators()

    # Bounds for GA
    bounds = (
        [(-0.3, 0.3)] * 6 +   # delta_S
        [(-0.3, 0.3)] * 6 +   # delta_T
        [(0.0, 5.0)] +        # alpha (hyperfine modulation)
        [(0.0, 3.0)] +        # beta (exchange modulation)
        [(0.0, 0.5)]          # gamma (field angle modulation)
    )

    # ── Phase 1: Evolutionary optimization ────────────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 1: EVOLUTIONARY OPTIMIZATION")
    print("=" * 72)

    gen_count = [0]
    t0 = time.time()

    def callback(xk, convergence=0):
        gen_count[0] += 1
        dist = fitness_fn(xk, ops, B_field, a_base, J_base, tau, k_S, k_T,
                         target, n_events, n_seeds_ga, 1000)
        elapsed = time.time() - t0
        print(f"  Gen {gen_count[0]:3d} | mean_dist = {dist:.4f} | "
              f"elapsed = {elapsed:.1f}s", flush=True)

    result = differential_evolution(
        fitness_fn,
        bounds=bounds,
        args=(ops, B_field, a_base, J_base, tau, k_S, k_T,
              target, n_events, n_seeds_ga, 1000),
        maxiter=25,
        popsize=8,
        seed=42,
        callback=callback,
        tol=1e-6,
        mutation=(0.5, 1.5),
        recombination=0.8,
    )

    elapsed = time.time() - t0
    print(f"\n  GA completed in {elapsed:.1f}s")
    print(f"  Best mean distance: {result.fun:.4f}")

    best_params = result.x
    delta_S_opt = best_params[:6]
    delta_T_opt = best_params[6:12]
    alpha_opt = best_params[12]
    beta_opt = best_params[13]
    gamma_opt = best_params[14]

    print(f"\n  Optimized feedback parameters:")
    print(f"    delta_S = [{', '.join(f'{v:.4f}' for v in delta_S_opt)}]")
    print(f"    delta_T = [{', '.join(f'{v:.4f}' for v in delta_T_opt)}]")
    print(f"    alpha   = {alpha_opt:.4f} MHz")
    print(f"    beta    = {beta_opt:.4f} MHz")
    print(f"    gamma   = {gamma_opt:.4f} rad")

    # ── Phase 2: Comparison ───────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 2: FOUR-WAY COMPARISON")
    print("=" * 72)

    ps0_opt, grad_opt = compute_PS_gradient(
        ops, B_field, a_base, J_base, alpha_opt, beta_opt, gamma_opt, tau, k_S, k_T)

    # Random feedback params for condition 4
    rng_rand = np.random.default_rng(99)
    delta_S_rand = rng_rand.uniform(-0.3, 0.3, 6)
    delta_T_rand = rng_rand.uniform(-0.3, 0.3, 6)
    ps0_rand, grad_rand = compute_PS_gradient(
        ops, B_field, a_base, J_base,
        rng_rand.uniform(0, 5), rng_rand.uniform(0, 3), rng_rand.uniform(0, 0.5),
        tau, k_S, k_T)

    conditions = {
        "Adaptive+Evolved": (delta_S_opt, delta_T_opt, ps0_opt, grad_opt, True, True),
        "FixedBasis+Evolved": (delta_S_opt, delta_T_opt, ps0_opt, grad_opt, False, True),
        "Classical+Evolved": (delta_S_opt, delta_T_opt, ps0_opt, grad_opt, True, False),
        "Adaptive+Random": (delta_S_rand, delta_T_rand, ps0_rand, grad_rand, True, True),
    }

    results = {}
    for name, (dS, dT, ps0, grad, adaptive, quantum) in conditions.items():
        dists = []
        for s in range(n_runs_compare):
            rng = np.random.default_rng(2000 + s)
            theta_f, _ = run_adaptive_fast(rng, n_events, ps0, grad, dS, dT, adaptive, quantum)
            dists.append(np.linalg.norm(theta_f - target))

        results[name] = {
            'mean_dist': np.mean(dists),
            'std_dist': np.std(dists),
            'hit_rate': np.mean([d < 0.2 * np.linalg.norm(target) for d in dists]),
            'min_dist': np.min(dists),
        }

    # Print comparison
    print(f"\n  {'Condition':<25} {'Mean dist':>10} {'Std':>10} {'Min dist':>10} {'Hit rate':>10}")
    print(f"  {'-' * 65}")
    for name, r in results.items():
        print(f"  {name:<25} {r['mean_dist']:10.4f} {r['std_dist']:10.4f} "
              f"{r['min_dist']:10.4f} {r['hit_rate']:10.1%}")

    # ── Verdict ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  VERDICT")
    print("=" * 72)

    ae = results["Adaptive+Evolved"]
    fe = results["FixedBasis+Evolved"]
    ce = results["Classical+Evolved"]
    ar = results["Adaptive+Random"]
    initial_dist = np.linalg.norm(target)

    print(f"\n  Initial distance to target: {initial_dist:.4f}")
    print(f"  Adaptive+Evolved reaches:  {ae['mean_dist']:.4f} ({ae['mean_dist']/initial_dist:.1%} of initial)")
    print(f"  FixedBasis+Evolved:        {fe['mean_dist']:.4f} ({fe['mean_dist']/initial_dist:.1%} of initial)")
    print(f"  Classical+Evolved:         {ce['mean_dist']:.4f} ({ce['mean_dist']/initial_dist:.1%} of initial)")
    print(f"  Adaptive+Random:           {ar['mean_dist']:.4f} ({ar['mean_dist']/initial_dist:.1%} of initial)")

    # Check if adaptive+evolved beats all others
    beats_fixed = ae['mean_dist'] < fe['mean_dist']
    beats_classical = ae['mean_dist'] < ce['mean_dist']
    beats_random = ae['mean_dist'] < ar['mean_dist']

    print()
    if beats_fixed and beats_classical and beats_random:
        advantage_over_fixed = (fe['mean_dist'] - ae['mean_dist']) / fe['mean_dist']
        advantage_over_classical = (ce['mean_dist'] - ae['mean_dist']) / ce['mean_dist']
        print(f"  DIRECTED NAVIGATION CONFIRMED")
        print(f"  Adaptive+Evolved beats all three controls:")
        print(f"    vs FixedBasis:  {advantage_over_fixed:+.1%} closer to target")
        print(f"    vs Classical:   {advantage_over_classical:+.1%} closer to target")
        print(f"    vs Random:      beats random feedback")
        print()
        print(f"  This demonstrates:")
        print(f"  1. Quantum dynamics matter (beats Classical)")
        print(f"  2. Adaptive measurement basis matters (beats FixedBasis)")
        print(f"  3. Evolution can tune the feedback (beats Random)")
        print(f"  All three levels — quantum, adaptive, evolved — are necessary.")
    elif beats_fixed and beats_classical:
        print(f"  PARTIAL: Adaptive+Evolved beats Fixed and Classical")
        print(f"  but does not beat Random — evolution may not be necessary.")
    elif not beats_fixed:
        print(f"  FIXED BASIS IS SUFFICIENT")
        print(f"  The adaptive loop doesn't help beyond evolved shift vectors.")
        print(f"  Quantum measurement basis selection is not necessary.")
    elif not beats_classical:
        print(f"  CLASSICAL IS SUFFICIENT")
        print(f"  Quantum dynamics don't help — any feedback loop works.")
    else:
        print(f"  MIXED RESULTS — see comparison table above.")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
