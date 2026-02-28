"""
Measurement Basis Selection Simulation — NFT Level B Core Test
==============================================================

Tests whether a system that UPDATES its measurement basis based on outcomes
navigates state space differently than one with a fixed basis.

Thesis: Consciousness navigates by choosing which quantum questions to ask,
not by biasing the answers. A system that updates its measurement basis
(which spin observable the environment couples to) based on each radical pair
outcome should explore state space differently than a system with a fixed
measurement basis — even though every individual outcome follows the Born
rule identically.

Model: Two electron spins + one nuclear spin (I=1), 12-dimensional Hilbert
space. Sequences of 500 radical pair events where measurement basis evolves
through a 6D conformational state vector.

Three conditions compared:
  1. Adaptive basis  — measurement basis updates after each outcome
  2. Fixed basis     — quantum dynamics with frozen Hamiltonian
  3. Classical       — biased coin flip, no quantum dynamics
"""

import numpy as np
from scipy.linalg import expm
from typing import Dict, List, Tuple
import time
import sys

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
MU_B = 9.274_010_0783e-24   # Bohr magneton  (J/T)
HBAR = 1.054_571_817e-34    # reduced Planck  (J s)
G_E  = 2.002_319_304        # free-electron g-factor

# ---------------------------------------------------------------------------
# Spin operator factories (from spin_coherence.py)
# ---------------------------------------------------------------------------

def _pauli():
    """Return Pauli matrices / 2 (spin-1/2 operators) and identity."""
    sx = np.array([[0, 1], [1, 0]], dtype=complex) / 2
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex) / 2
    sz = np.array([[1, 0], [0, -1]], dtype=complex) / 2
    identity = np.eye(2, dtype=complex)
    return sx, sy, sz, identity


def _spin1():
    """Return spin-1 operators Ix, Iy, Iz and 3x3 identity."""
    sq2 = np.sqrt(2.0)
    ix = np.array([[0, 1, 0],
                   [1, 0, 1],
                   [0, 1, 0]], dtype=complex) / sq2
    iy = np.array([[0, -1j, 0],
                   [1j, 0, -1j],
                   [0, 1j, 0]], dtype=complex) / sq2
    iz = np.array([[1, 0, 0],
                   [0, 0, 0],
                   [0, 0, -1]], dtype=complex)
    identity = np.eye(3, dtype=complex)
    return ix, iy, iz, identity


def build_operators():
    """Build all 12x12 spin operators for electron1 x electron2 x nucleus."""
    sx, sy, sz, I2 = _pauli()
    Ix, Iy, Iz, I3 = _spin1()

    def kron3(A, B, C):
        return np.kron(np.kron(A, B), C)

    S1x = kron3(sx, I2, I3)
    S1y = kron3(sy, I2, I3)
    S1z = kron3(sz, I2, I3)
    S2x = kron3(I2, sx, I3)
    S2y = kron3(I2, sy, I3)
    S2z = kron3(I2, sz, I3)
    INx = kron3(I2, I2, Ix)
    INy = kron3(I2, I2, Iy)
    INz = kron3(I2, I2, Iz)
    I12 = np.eye(12, dtype=complex)

    return {
        'S1x': S1x, 'S1y': S1y, 'S1z': S1z,
        'S2x': S2x, 'S2y': S2y, 'S2z': S2z,
        'INx': INx, 'INy': INy, 'INz': INz,
        'I12': I12,
    }


def build_singlet_projector(ops: dict) -> np.ndarray:
    """Singlet projector on electron subspace, tensored with nuclear identity."""
    S1S2 = (ops['S1x'] @ ops['S2x']
            + ops['S1y'] @ ops['S2y']
            + ops['S1z'] @ ops['S2z'])
    P_S = 0.25 * ops['I12'] - S1S2
    return P_S


# ---------------------------------------------------------------------------
# Hamiltonian construction with conformation-dependent parameters
# ---------------------------------------------------------------------------

def build_hamiltonian(ops: dict,
                      B_field: float = 50e-6,
                      a_N_MHz: float = 10.0,
                      J_MHz: float = 0.0,
                      phi_rad: float = 0.0) -> np.ndarray:
    """
    Build the spin Hamiltonian in rad/us units with a tilted magnetic field.

    The effective field direction is determined by phi_rad:
      B_eff = B * (sin(phi) * x_hat + cos(phi) * z_hat)

    Parameters:
        B_field  : magnetic field magnitude (T)
        a_N_MHz  : hyperfine coupling (MHz)
        J_MHz    : exchange coupling (MHz)
        phi_rad  : tilt angle of effective field from z-axis (rad)
    """
    # Zeeman frequency
    omega = G_E * MU_B * B_field / HBAR  # rad/s
    omega_rad_us = omega * 1e-6          # rad/us

    # Couplings in rad/us
    a_N = 2.0 * np.pi * a_N_MHz
    J = 2.0 * np.pi * J_MHz

    # Zeeman terms with tilted field
    cos_phi = np.cos(phi_rad)
    sin_phi = np.sin(phi_rad)
    H = omega_rad_us * (
        cos_phi * (ops['S1z'] + ops['S2z'])
        + sin_phi * (ops['S1x'] + ops['S2x'])
    )

    # Hyperfine coupling: a_N * S1 . I_N
    H += a_N * (ops['S1x'] @ ops['INx']
                + ops['S1y'] @ ops['INy']
                + ops['S1z'] @ ops['INz'])

    # Exchange coupling: J * S1 . S2
    S1S2 = (ops['S1x'] @ ops['S2x']
            + ops['S1y'] @ ops['S2y']
            + ops['S1z'] @ ops['S2z'])
    H += J * S1S2

    return H


# ---------------------------------------------------------------------------
# Liouvillian (superoperator) construction
# ---------------------------------------------------------------------------

def _commutator_superop(H: np.ndarray) -> np.ndarray:
    n = H.shape[0]
    I_n = np.eye(n, dtype=complex)
    return -1j * (np.kron(H, I_n) - np.kron(I_n, H.T))


def _anticommutator_superop(A: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    I_n = np.eye(n, dtype=complex)
    return np.kron(A, I_n) + np.kron(I_n, A.T)


def _lindblad_dephasing_superop(Sz: np.ndarray, gamma: float) -> np.ndarray:
    n = Sz.shape[0]
    I_n = np.eye(n, dtype=complex)
    Sz2 = Sz @ Sz
    L = gamma * (np.kron(Sz, Sz.conj())
                 - 0.5 * np.kron(Sz2, I_n)
                 - 0.5 * np.kron(I_n, Sz2.T))
    return L


def build_liouvillian(H: np.ndarray,
                      P_S: np.ndarray,
                      ops: dict,
                      k_S: float = 1.0,
                      k_T: float = 0.1,
                      T2: float = 1.0) -> np.ndarray:
    """Build full Liouvillian superoperator (144 x 144)."""
    P_T = ops['I12'] - P_S

    L = _commutator_superop(H)
    L -= (k_S / 2.0) * _anticommutator_superop(P_S)
    L -= (k_T / 2.0) * _anticommutator_superop(P_T)

    gamma = 1.0 / T2
    L += _lindblad_dephasing_superop(ops['S1z'], gamma)
    L += _lindblad_dephasing_superop(ops['S2z'], gamma)

    return L


# ---------------------------------------------------------------------------
# Core simulation: single radical pair event
# ---------------------------------------------------------------------------

def compute_singlet_probability(ops: dict, P_S: np.ndarray,
                                 B_field: float, a_N_MHz: float,
                                 J_MHz: float, phi_rad: float,
                                 k_S: float, k_T: float, T2: float,
                                 tau: float) -> float:
    """
    Evolve singlet initial state for time tau under the given Hamiltonian
    parameters and return the singlet probability at time tau.

    Uses Liouvillian (density matrix) evolution to properly account for
    decoherence and decay.
    """
    H = build_hamiltonian(ops, B_field=B_field, a_N_MHz=a_N_MHz,
                          J_MHz=J_MHz, phi_rad=phi_rad)
    L = build_liouvillian(H, P_S, ops, k_S=k_S, k_T=k_T, T2=T2)

    # Initial state: normalized singlet projection
    rho0 = P_S / np.real(np.trace(P_S))
    rho_vec = rho0.flatten(order='C')

    # Propagate
    U = expm(L * tau)
    rho_vec_final = U @ rho_vec
    rho_final = rho_vec_final.reshape((12, 12), order='C')

    # Singlet probability (normalized by surviving population)
    pop = np.real(np.trace(rho_final))
    p_s_raw = np.real(np.trace(rho_final @ P_S))

    if pop > 1e-12:
        return np.clip(p_s_raw / pop, 0.0, 1.0)
    else:
        return 0.5  # fallback if all population decayed


# ---------------------------------------------------------------------------
# Conformation-to-Hamiltonian mapping
# ---------------------------------------------------------------------------

def theta_to_hamiltonian_params(theta: np.ndarray,
                                 a_base: float = 10.0,
                                 J_base: float = 0.0,
                                 phi_base: float = 0.0,
                                 alpha: float = 2.0,
                                 beta: float = 1.0,
                                 gamma_angle: float = 0.2
                                 ) -> Tuple[float, float, float]:
    """
    Map conformational state theta to Hamiltonian parameters.

    theta[0] modulates hyperfine coupling
    theta[1] modulates exchange coupling
    theta[2] modulates effective field tilt angle
    """
    a_N = a_base + alpha * theta[0]
    J = J_base + beta * theta[1]
    phi = phi_base + gamma_angle * theta[2]
    return a_N, J, phi


# ---------------------------------------------------------------------------
# Run a single trajectory (one condition, one seed)
# ---------------------------------------------------------------------------

def run_trajectory_adaptive(rng: np.random.Generator,
                             ops: dict, P_S: np.ndarray,
                             N_events: int, tau: float,
                             B_field: float, k_S: float, k_T: float,
                             T2: float, delta_S: np.ndarray,
                             delta_T: np.ndarray,
                             a_base: float, J_base: float,
                             alpha: float, beta: float,
                             gamma_angle: float
                             ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Adaptive basis condition: theta feeds back into Hamiltonian.

    Returns:
        theta_history: (N_events+1, 6) array of conformational states
        outcomes: (N_events,) array of outcomes (1=singlet, 0=triplet)
    """
    N_conf = 6
    theta = np.zeros(N_conf)
    theta_history = np.zeros((N_events + 1, N_conf))
    theta_history[0] = theta.copy()
    outcomes = np.zeros(N_events, dtype=int)

    for i in range(N_events):
        # Map conformation to Hamiltonian parameters
        a_N, J, phi = theta_to_hamiltonian_params(
            theta, a_base=a_base, J_base=J_base,
            alpha=alpha, beta=beta, gamma_angle=gamma_angle
        )

        # Compute singlet probability from quantum dynamics
        p_s = compute_singlet_probability(
            ops, P_S, B_field=B_field, a_N_MHz=a_N,
            J_MHz=J, phi_rad=phi, k_S=k_S, k_T=k_T, T2=T2, tau=tau
        )

        # Stochastic measurement outcome (Born rule)
        outcome = 1 if rng.random() < p_s else 0
        outcomes[i] = outcome

        # Conformational update (back-action)
        if outcome == 1:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

        theta_history[i + 1] = theta.copy()

    return theta_history, outcomes


def run_trajectory_fixed(rng: np.random.Generator,
                          ops: dict, P_S: np.ndarray,
                          N_events: int, tau: float,
                          B_field: float, k_S: float, k_T: float,
                          T2: float, delta_S: np.ndarray,
                          delta_T: np.ndarray,
                          a_base: float, J_base: float
                          ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fixed basis condition: theta is frozen at zero for Hamiltonian,
    but conformational shifts still accumulate for tracking.

    Returns:
        theta_history: (N_events+1, 6) array of conformational states
        outcomes: (N_events,) array of outcomes
    """
    N_conf = 6
    theta = np.zeros(N_conf)
    theta_history = np.zeros((N_events + 1, N_conf))
    theta_history[0] = theta.copy()
    outcomes = np.zeros(N_events, dtype=int)

    # Compute singlet probability ONCE with fixed parameters
    p_s_fixed = compute_singlet_probability(
        ops, P_S, B_field=B_field, a_N_MHz=a_base,
        J_MHz=J_base, phi_rad=0.0, k_S=k_S, k_T=k_T, T2=T2, tau=tau
    )

    for i in range(N_events):
        # Same quantum probability every time (fixed basis)
        outcome = 1 if rng.random() < p_s_fixed else 0
        outcomes[i] = outcome

        # Conformational update still happens (for tracking)
        if outcome == 1:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

        theta_history[i + 1] = theta.copy()

    return theta_history, outcomes


def run_trajectory_classical(rng: np.random.Generator,
                              N_events: int, p_s_classical: float,
                              delta_S: np.ndarray,
                              delta_T: np.ndarray
                              ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Classical condition: biased coin flip, no quantum dynamics.

    Returns:
        theta_history: (N_events+1, 6) array of conformational states
        outcomes: (N_events,) array of outcomes
    """
    N_conf = 6
    theta = np.zeros(N_conf)
    theta_history = np.zeros((N_events + 1, N_conf))
    theta_history[0] = theta.copy()
    outcomes = np.zeros(N_events, dtype=int)

    for i in range(N_events):
        outcome = 1 if rng.random() < p_s_classical else 0
        outcomes[i] = outcome

        if outcome == 1:
            theta = theta + delta_S
        else:
            theta = theta + delta_T

        theta_history[i + 1] = theta.copy()

    return theta_history, outcomes


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(all_theta_finals: np.ndarray,
                    all_outcomes: np.ndarray,
                    all_theta_histories: np.ndarray
                    ) -> dict:
    """
    Compute all comparison metrics for a set of runs.

    Parameters:
        all_theta_finals: (N_runs, 6) final theta vectors
        all_outcomes: (N_runs, N_events) outcome sequences
        all_theta_histories: (N_runs, N_events+1, 6) full trajectories
    """
    N_runs = all_theta_finals.shape[0]

    # 1. Final position statistics
    norms = np.linalg.norm(all_theta_finals, axis=1)
    mean_norm = np.mean(norms)
    std_norm = np.std(norms)

    # 2. Directional consistency (mean pairwise cosine similarity)
    # Normalize final vectors
    nonzero = norms > 1e-10
    if np.sum(nonzero) > 1:
        dirs = all_theta_finals[nonzero] / norms[nonzero, np.newaxis]
        n_valid = dirs.shape[0]
        # Compute pairwise cosine similarities
        cos_sim_sum = 0.0
        n_pairs = 0
        for i in range(n_valid):
            for j in range(i + 1, n_valid):
                cos_sim_sum += np.dot(dirs[i], dirs[j])
                n_pairs += 1
        mean_cosine_sim = cos_sim_sum / n_pairs if n_pairs > 0 else 0.0
    else:
        mean_cosine_sim = 0.0

    # 3. Outcome autocorrelation (lag-1)
    autocorrs = []
    for run_idx in range(N_runs):
        outcomes = all_outcomes[run_idx]
        if len(outcomes) > 1:
            o_centered = outcomes - np.mean(outcomes)
            var = np.var(outcomes)
            if var > 1e-12:
                autocorr = np.mean(o_centered[:-1] * o_centered[1:]) / var
                autocorrs.append(autocorr)
    mean_autocorr = np.mean(autocorrs) if autocorrs else 0.0

    # 4. Exploration entropy
    # Discretize final theta positions into bins and compute entropy
    # Use 10 bins per dimension, but project to 2D (first two principal components)
    # for tractability. Actually, just use the norm distribution.
    n_bins = 20
    norm_min = np.min(norms)
    norm_max = np.max(norms)
    if norm_max - norm_min > 1e-10:
        hist, _ = np.histogram(norms, bins=n_bins, range=(norm_min, norm_max))
        # Normalize
        hist_norm = hist / np.sum(hist)
        # Entropy
        nonzero_bins = hist_norm > 0
        entropy = -np.sum(hist_norm[nonzero_bins] * np.log2(hist_norm[nonzero_bins]))
    else:
        entropy = 0.0

    # 5. Mean direction
    mean_final = np.mean(all_theta_finals, axis=0)
    mean_final_norm = np.linalg.norm(mean_final)
    if mean_final_norm > 1e-10:
        mean_direction = mean_final / mean_final_norm
    else:
        mean_direction = np.zeros(6)

    return {
        'mean_norm': mean_norm,
        'std_norm': std_norm,
        'mean_cosine_sim': mean_cosine_sim,
        'mean_autocorr': mean_autocorr,
        'exploration_entropy': entropy,
        'mean_direction': mean_direction,
    }


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("  MEASUREMENT BASIS SELECTION SIMULATION")
    print("  NFT Level B Core Test: Adaptive vs Fixed vs Classical")
    print("  Hilbert space: 2 x 2 x 3 = 12 dimensions")
    print("=" * 78)

    # ----- Parameters -----
    B_field = 50e-6        # T (Earth's field)
    a_base = 10.0          # MHz
    J_base = 0.0           # MHz
    k_S = 1.0              # us^-1
    k_T = 0.1              # us^-1
    T2 = 1.0               # us
    tau = 1.0              # us (radical pair lifetime per event)
    N_events = 500         # events per trajectory
    N_runs = 200           # trajectories per condition

    # Conformational modulation strengths
    alpha = 2.0            # MHz per unit theta[0]
    beta = 1.0             # MHz per unit theta[1]
    gamma_angle = 0.2      # rad per unit theta[2]

    # Conformational shifts upon measurement outcome
    delta_S = np.array([+0.1, -0.05, +0.02, -0.03, +0.01, -0.02])
    delta_T = np.array([-0.08, +0.06, -0.03, +0.04, -0.02, +0.01])

    print("\n--- Parameters ---")
    print(f"  B_field       : {B_field*1e6:.0f} uT")
    print(f"  a_base        : {a_base} MHz")
    print(f"  J_base        : {J_base} MHz")
    print(f"  k_S           : {k_S} us^-1")
    print(f"  k_T           : {k_T} us^-1")
    print(f"  T2            : {T2} us")
    print(f"  tau (lifetime): {tau} us")
    print(f"  N_events      : {N_events}")
    print(f"  N_runs        : {N_runs}")
    print(f"  alpha         : {alpha} MHz")
    print(f"  beta          : {beta} MHz")
    print(f"  gamma         : {gamma_angle} rad")
    print(f"  delta_S       : {delta_S}")
    print(f"  delta_T       : {delta_T}")

    # ----- Build operators (shared across all runs) -----
    print("\nBuilding spin operators...", flush=True)
    ops = build_operators()
    P_S = build_singlet_projector(ops)

    # ----- Compute fixed-basis singlet probability (used by Fixed and Classical) -----
    print("Computing fixed-basis singlet probability...", flush=True)
    p_s_fixed = compute_singlet_probability(
        ops, P_S, B_field=B_field, a_N_MHz=a_base,
        J_MHz=J_base, phi_rad=0.0, k_S=k_S, k_T=k_T, T2=T2, tau=tau
    )
    print(f"  P_S(fixed basis, tau={tau} us) = {p_s_fixed:.6f}")

    # ===================================================================
    # CONDITION 1: ADAPTIVE BASIS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  CONDITION 1: ADAPTIVE BASIS ({N_runs} runs x {N_events} events)")
    print(f"{'='*78}")

    adaptive_finals = np.zeros((N_runs, 6))
    adaptive_outcomes = np.zeros((N_runs, N_events), dtype=int)
    adaptive_histories = np.zeros((N_runs, N_events + 1, 6))

    t_start = time.time()
    for run in range(N_runs):
        if (run + 1) % 20 == 0 or run == 0:
            elapsed = time.time() - t_start
            if run > 0:
                eta = elapsed / run * (N_runs - run)
                print(f"  Run {run+1}/{N_runs}  (elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s)",
                      flush=True)
            else:
                print(f"  Run {run+1}/{N_runs}...", flush=True)

        rng = np.random.default_rng(seed=42 + run)
        theta_hist, outcomes = run_trajectory_adaptive(
            rng, ops, P_S, N_events, tau,
            B_field, k_S, k_T, T2, delta_S, delta_T,
            a_base, J_base, alpha, beta, gamma_angle
        )
        adaptive_finals[run] = theta_hist[-1]
        adaptive_outcomes[run] = outcomes
        adaptive_histories[run] = theta_hist

    t_adaptive = time.time() - t_start
    print(f"  Adaptive condition completed in {t_adaptive:.1f}s")

    # ===================================================================
    # CONDITION 2: FIXED BASIS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  CONDITION 2: FIXED BASIS ({N_runs} runs x {N_events} events)")
    print(f"{'='*78}")

    fixed_finals = np.zeros((N_runs, 6))
    fixed_outcomes = np.zeros((N_runs, N_events), dtype=int)
    fixed_histories = np.zeros((N_runs, N_events + 1, 6))

    t_start = time.time()
    for run in range(N_runs):
        if (run + 1) % 50 == 0 or run == 0:
            print(f"  Run {run+1}/{N_runs}...", flush=True)

        rng = np.random.default_rng(seed=42 + run)
        theta_hist, outcomes = run_trajectory_fixed(
            rng, ops, P_S, N_events, tau,
            B_field, k_S, k_T, T2, delta_S, delta_T,
            a_base, J_base
        )
        fixed_finals[run] = theta_hist[-1]
        fixed_outcomes[run] = outcomes
        fixed_histories[run] = theta_hist

    t_fixed = time.time() - t_start
    print(f"  Fixed condition completed in {t_fixed:.1f}s")

    # ===================================================================
    # CONDITION 3: CLASSICAL (coin flip)
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  CONDITION 3: CLASSICAL ({N_runs} runs x {N_events} events)")
    print(f"{'='*78}")

    # Use the fixed-basis P_S as the classical coin bias
    p_s_classical = p_s_fixed
    print(f"  Classical bias P_S = {p_s_classical:.6f}")

    classical_finals = np.zeros((N_runs, 6))
    classical_outcomes = np.zeros((N_runs, N_events), dtype=int)
    classical_histories = np.zeros((N_runs, N_events + 1, 6))

    t_start = time.time()
    for run in range(N_runs):
        rng = np.random.default_rng(seed=42 + run)
        theta_hist, outcomes = run_trajectory_classical(
            rng, N_events, p_s_classical, delta_S, delta_T
        )
        classical_finals[run] = theta_hist[-1]
        classical_outcomes[run] = outcomes
        classical_histories[run] = theta_hist

    t_classical = time.time() - t_start
    print(f"  Classical condition completed in {t_classical:.1f}s")

    # ===================================================================
    # COMPUTE METRICS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  COMPUTING METRICS")
    print(f"{'='*78}")

    metrics_adaptive = compute_metrics(adaptive_finals, adaptive_outcomes,
                                        adaptive_histories)
    metrics_fixed = compute_metrics(fixed_finals, fixed_outcomes,
                                     fixed_histories)
    metrics_classical = compute_metrics(classical_finals, classical_outcomes,
                                         classical_histories)

    # ===================================================================
    # RESULTS TABLE
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  RESULTS: COMPARISON TABLE")
    print(f"{'='*78}\n")

    header = f"{'Metric':<40s} {'Adaptive':>12s} {'Fixed Basis':>12s} {'Classical':>12s}"
    print(header)
    print("-" * len(header))

    rows = [
        ("Mean ||theta_final||",
         metrics_adaptive['mean_norm'],
         metrics_fixed['mean_norm'],
         metrics_classical['mean_norm']),
        ("Std ||theta_final||",
         metrics_adaptive['std_norm'],
         metrics_fixed['std_norm'],
         metrics_classical['std_norm']),
        ("Direction consistency (cosine sim)",
         metrics_adaptive['mean_cosine_sim'],
         metrics_fixed['mean_cosine_sim'],
         metrics_classical['mean_cosine_sim']),
        ("Outcome autocorrelation (lag-1)",
         metrics_adaptive['mean_autocorr'],
         metrics_fixed['mean_autocorr'],
         metrics_classical['mean_autocorr']),
        ("Exploration entropy (bits)",
         metrics_adaptive['exploration_entropy'],
         metrics_fixed['exploration_entropy'],
         metrics_classical['exploration_entropy']),
    ]

    for name, v_a, v_f, v_c in rows:
        print(f"{name:<40s} {v_a:>12.6f} {v_f:>12.6f} {v_c:>12.6f}")

    # Mean direction vectors
    print(f"\n--- Mean Final Direction Vectors ---")
    print(f"  Adaptive : [{', '.join(f'{x:+.4f}' for x in metrics_adaptive['mean_direction'])}]")
    print(f"  Fixed    : [{', '.join(f'{x:+.4f}' for x in metrics_fixed['mean_direction'])}]")
    print(f"  Classical: [{', '.join(f'{x:+.4f}' for x in metrics_classical['mean_direction'])}]")

    # Mean final theta (not just direction)
    print(f"\n--- Mean Final Theta Vectors ---")
    mean_a = np.mean(adaptive_finals, axis=0)
    mean_f = np.mean(fixed_finals, axis=0)
    mean_c = np.mean(classical_finals, axis=0)
    print(f"  Adaptive : [{', '.join(f'{x:+.4f}' for x in mean_a)}]")
    print(f"  Fixed    : [{', '.join(f'{x:+.4f}' for x in mean_f)}]")
    print(f"  Classical: [{', '.join(f'{x:+.4f}' for x in mean_c)}]")

    # ===================================================================
    # DETAILED ANALYSIS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  DETAILED ANALYSIS")
    print(f"{'='*78}")

    # Singlet fraction per condition
    mean_singlet_adaptive = np.mean(adaptive_outcomes)
    mean_singlet_fixed = np.mean(fixed_outcomes)
    mean_singlet_classical = np.mean(classical_outcomes)
    print(f"\n  Mean singlet fraction:")
    print(f"    Adaptive  : {mean_singlet_adaptive:.6f}")
    print(f"    Fixed     : {mean_singlet_fixed:.6f}")
    print(f"    Classical : {mean_singlet_classical:.6f}")

    # Outcome autocorrelation at multiple lags
    print(f"\n  Outcome autocorrelation at multiple lags:")
    for lag in [1, 2, 5, 10, 20]:
        ac_a = []
        ac_f = []
        ac_c = []
        for run_idx in range(N_runs):
            for oc, ac_list in [(adaptive_outcomes, ac_a),
                                 (fixed_outcomes, ac_f),
                                 (classical_outcomes, ac_c)]:
                o = oc[run_idx]
                o_c = o - np.mean(o)
                var = np.var(o)
                if var > 1e-12 and len(o) > lag:
                    ac_list.append(np.mean(o_c[:-lag] * o_c[lag:]) / var)
        print(f"    Lag {lag:>2d}:  Adaptive={np.mean(ac_a):+.6f}  "
              f"Fixed={np.mean(ac_f):+.6f}  Classical={np.mean(ac_c):+.6f}")

    # Trajectory divergence: when do adaptive trajectories start differing
    # from fixed/classical?
    print(f"\n  Trajectory norm evolution (mean across runs):")
    checkpoints = [0, 50, 100, 200, 300, 400, 500]
    print(f"    {'Step':>6s}  {'Adaptive':>12s}  {'Fixed':>12s}  {'Classical':>12s}")
    for step in checkpoints:
        if step <= N_events:
            norm_a = np.mean(np.linalg.norm(adaptive_histories[:, step, :], axis=1))
            norm_f = np.mean(np.linalg.norm(fixed_histories[:, step, :], axis=1))
            norm_c = np.mean(np.linalg.norm(classical_histories[:, step, :], axis=1))
            print(f"    {step:>6d}  {norm_a:>12.4f}  {norm_f:>12.4f}  {norm_c:>12.4f}")

    # ===================================================================
    # STATISTICAL SIGNIFICANCE
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  STATISTICAL SIGNIFICANCE TESTS")
    print(f"{'='*78}")

    # Compare adaptive vs fixed norms
    from scipy import stats

    norms_a = np.linalg.norm(adaptive_finals, axis=1)
    norms_f = np.linalg.norm(fixed_finals, axis=1)
    norms_c = np.linalg.norm(classical_finals, axis=1)

    t_af, p_af = stats.ttest_ind(norms_a, norms_f)
    t_ac, p_ac = stats.ttest_ind(norms_a, norms_c)
    t_fc, p_fc = stats.ttest_ind(norms_f, norms_c)

    print(f"\n  Two-sample t-test on ||theta_final||:")
    print(f"    Adaptive vs Fixed    : t={t_af:+.4f}, p={p_af:.2e}")
    print(f"    Adaptive vs Classical: t={t_ac:+.4f}, p={p_ac:.2e}")
    print(f"    Fixed vs Classical   : t={t_fc:+.4f}, p={p_fc:.2e}")

    # Compare cosine similarities
    # Recompute pairwise cosine sims for each condition to get distributions
    def pairwise_cosine_sample(finals, n_sample=500):
        """Sample pairwise cosine similarities."""
        norms = np.linalg.norm(finals, axis=1)
        valid = norms > 1e-10
        dirs = finals[valid] / norms[valid, np.newaxis]
        n = dirs.shape[0]
        if n < 2:
            return np.array([0.0])
        sims = []
        rng_s = np.random.default_rng(99)
        for _ in range(min(n_sample, n * (n - 1) // 2)):
            i, j = rng_s.choice(n, size=2, replace=False)
            sims.append(np.dot(dirs[i], dirs[j]))
        return np.array(sims)

    cos_a = pairwise_cosine_sample(adaptive_finals)
    cos_f = pairwise_cosine_sample(fixed_finals)
    cos_c = pairwise_cosine_sample(classical_finals)

    t_cos_af, p_cos_af = stats.ttest_ind(cos_a, cos_f)
    print(f"\n  Two-sample t-test on cosine similarity:")
    print(f"    Adaptive vs Fixed    : t={t_cos_af:+.4f}, p={p_cos_af:.2e}")

    # ===================================================================
    # VERDICT
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  VERDICT")
    print(f"{'='*78}")

    # Determine if adaptive shows measurably different navigation
    cos_diff = metrics_adaptive['mean_cosine_sim'] - metrics_fixed['mean_cosine_sim']
    autocorr_diff = metrics_adaptive['mean_autocorr'] - metrics_fixed['mean_autocorr']
    norm_diff = metrics_adaptive['mean_norm'] - metrics_fixed['mean_norm']

    print(f"\n  Key differences (Adaptive - Fixed):")
    print(f"    Direction consistency:  {cos_diff:+.6f}")
    print(f"    Outcome autocorrelation: {autocorr_diff:+.6f}")
    print(f"    Mean final norm:        {norm_diff:+.6f}")

    # Assess
    adaptive_navigates = False
    reasons = []

    if abs(cos_diff) > 0.001 and p_cos_af < 0.05:
        if cos_diff > 0:
            reasons.append("HIGHER directional consistency (converges toward specific regions)")
        else:
            reasons.append("LOWER directional consistency (explores more broadly)")
        adaptive_navigates = True

    if abs(autocorr_diff) > 0.001:
        if autocorr_diff > 0:
            reasons.append("HIGHER outcome autocorrelation (feedback creates temporal structure)")
        else:
            reasons.append("outcome autocorrelation structure differs from fixed basis")
        adaptive_navigates = True

    if abs(norm_diff) > 0.1 and p_af < 0.05:
        reasons.append(f"Significantly different displacement in conformation space "
                       f"(p={p_af:.2e})")
        adaptive_navigates = True

    if adaptive_navigates:
        print(f"\n  >>> ADAPTIVE MEASUREMENT BASIS PRODUCES MEASURABLY DIFFERENT NAVIGATION <<<")
        print(f"\n  Evidence:")
        for r in reasons:
            print(f"    - {r}")
        print(f"\n  INTERPRETATION:")
        print(f"    The system that updates which quantum question it asks (measurement")
        print(f"    basis) based on previous answers navigates conformation space")
        print(f"    differently than a system with a fixed basis. This demonstrates that")
        print(f"    measurement-basis selection IS a form of navigation, supporting")
        print(f"    NFT's revised Level B claim: consciousness navigates by choosing")
        print(f"    which questions to ask, not by biasing the answers.")
    else:
        print(f"\n  >>> NO SIGNIFICANT DIFFERENCE DETECTED <<<")
        print(f"\n  The adaptive measurement basis does not produce measurably different")
        print(f"  navigation compared to fixed basis or classical conditions with the")
        print(f"  current parameters. This suggests that measurement-basis selection")
        print(f"  alone, at these modulation strengths, does not constitute effective")
        print(f"  navigation of state space.")

    print(f"\n  Total simulation time: Adaptive={t_adaptive:.1f}s, Fixed={t_fixed:.1f}s, "
          f"Classical={t_classical:.1f}s")
    print(f"{'='*78}\n")


if __name__ == "__main__":
    main()
