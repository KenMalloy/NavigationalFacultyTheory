"""
Directed Navigation via Evolved Measurement-Basis Feedback — JAX-Accelerated
=============================================================================

JAX-accelerated version of directed_navigation.py.

Key speedup strategy:
  - @jax.jit compiles the 300-event inner loop into optimized XLA code
  - jax.vmap batches across seeds (all seeds run as a single vectorized call)
  - jax.lax.scan replaces the Python for-loop over events
  - The GA calls the vmapped/jitted function, so each fitness evaluation
    is a single compiled kernel launch

Spin physics: 2 electrons + 1 nuclear spin (I=1), 12D Hilbert space.
Hamiltonian includes Zeeman, hyperfine (S1·I), and exchange (S1·S2) terms.
Singlet probability computed via coherent propagation (eigendecomposition).
"""

import os
import time
import warnings
from functools import partial

# ---------------------------------------------------------------------------
# JAX setup — Metal does not support complex numbers, so force CPU.
# JIT compilation alone provides large speedups even on CPU.
# ---------------------------------------------------------------------------
os.environ["JAX_PLATFORMS"] = "cpu"

import jax
import jax.numpy as jnp
import numpy as np
from scipy.optimize import differential_evolution

_PLATFORM = "cpu"
print(f"[JAX] Using platform: {_PLATFORM} (Metal lacks complex number support)")
print(f"[JAX] Devices: {jax.devices()}")

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
MU_B = 9.274_010_0783e-24   # Bohr magneton  (J/T)
HBAR = 1.054_571_817e-34    # reduced Planck  (J s)
G_E  = 2.002_319_304        # free-electron g-factor

# ---------------------------------------------------------------------------
# Simulation parameters
# ---------------------------------------------------------------------------
B_FIELD = 50e-6      # T (Earth's field)
A_BASE  = 10.0       # MHz
J_BASE  = 0.0        # MHz
K_S     = 1.0        # us^-1
K_T     = 0.1        # us^-1
T2      = 1.0        # us
TAU     = 1.0        # us
GAMMA_DEPH = 1.0 / T2  # us^-1

# Derived: Zeeman frequency in rad/us
OMEGA_Z = G_E * MU_B * B_FIELD / HBAR * 1e-6  # rad/us

# Fitness target
THETA_TARGET = np.array([3.0, -2.0, 1.5, -1.0, 2.0, -0.5])

# GA settings
N_EVENTS_GA    = 300
N_SEEDS_GA     = 20
GA_MAXITER     = 30
GA_POPSIZE     = 10
GA_SEED        = 42

# Comparison settings
N_EVENTS_COMP  = 300
N_RUNS_COMP    = 200

# Parameter bounds (same as original)
BOUNDS = (
    [(-0.3, 0.3)] * 6 +    # delta_S
    [(-0.3, 0.3)] * 6 +    # delta_T
    [(0.0, 5.0)] +          # alpha
    [(0.0, 3.0)] +          # beta
    [(0.0, 0.5)]            # gamma
)


# ---------------------------------------------------------------------------
# Spin operators — built once as JAX arrays
# ---------------------------------------------------------------------------

def build_spin_operators():
    """Build all 12x12 spin operators as JAX complex128 arrays.

    Returns a dict of JAX arrays for the spin operators and singlet projector.
    """
    # Pauli / 2 (spin-1/2)
    sx = np.array([[0, 1], [1, 0]], dtype=complex) / 2
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex) / 2
    sz = np.array([[1, 0], [0, -1]], dtype=complex) / 2
    I2 = np.eye(2, dtype=complex)

    # Spin-1 matrices
    sq2 = np.sqrt(2.0)
    Ix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / sq2
    Iy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / sq2
    Iz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
    I3 = np.eye(3, dtype=complex)

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

    # Singlet projector: P_S = (1/4)I - S1·S2
    S1S2 = S1x @ S2x + S1y @ S2y + S1z @ S2z
    P_S = 0.25 * I12 - S1S2

    # Initial state: normalized singlet projection
    rho0 = P_S / np.real(np.trace(P_S))

    # Convert everything to JAX arrays
    return {
        'S1x': jnp.array(S1x), 'S1y': jnp.array(S1y), 'S1z': jnp.array(S1z),
        'S2x': jnp.array(S2x), 'S2y': jnp.array(S2y), 'S2z': jnp.array(S2z),
        'INx': jnp.array(INx), 'INy': jnp.array(INy), 'INz': jnp.array(INz),
        'I12': jnp.array(I12),
        'P_S': jnp.array(P_S),
        'rho0': jnp.array(rho0),
        # Pre-compute products for Hamiltonian construction
        'S1x_INx': jnp.array(S1x @ INx),
        'S1y_INy': jnp.array(S1y @ INy),
        'S1z_INz': jnp.array(S1z @ INz),
        'S1S2': jnp.array(S1S2),
        'S1z_plus_S2z': jnp.array(S1z + S2z),
        'S1x_plus_S2x': jnp.array(S1x + S2x),
    }


# ---------------------------------------------------------------------------
# Hamiltonian and singlet probability — pure JAX functions
# ---------------------------------------------------------------------------

def build_hamiltonian_jax(a_N_rad, J_rad, phi, omega_z, spin_ops):
    """Build 12x12 spin Hamiltonian in rad/us.

    Args:
        a_N_rad: hyperfine coupling in rad/us (already multiplied by 2*pi)
        J_rad: exchange coupling in rad/us (already multiplied by 2*pi)
        phi: field tilt angle in radians
        omega_z: Zeeman frequency in rad/us
        spin_ops: dict of JAX arrays
    """
    cos_phi = jnp.cos(phi)
    sin_phi = jnp.sin(phi)

    # Zeeman with tilted field
    H = omega_z * (cos_phi * spin_ops['S1z_plus_S2z']
                   + sin_phi * spin_ops['S1x_plus_S2x'])

    # Hyperfine: a_N * S1 · I
    H = H + a_N_rad * (spin_ops['S1x_INx']
                       + spin_ops['S1y_INy']
                       + spin_ops['S1z_INz'])

    # Exchange: J * S1 · S2
    H = H + J_rad * spin_ops['S1S2']

    return H


def compute_singlet_prob_jax(H, P_S, rho0, tau):
    """Compute singlet probability via coherent eigendecomposition.

    Uses the Hermitian eigendecomposition approach:
      1. Diagonalize H (Hermitian)
      2. U(t) = V @ diag(exp(-i*E*t)) @ V†
      3. rho(t) = U(t) @ rho0 @ U(t)†
      4. P_S = Tr(P_S @ rho(t))

    This captures coherent singlet-triplet interconversion driven by the
    Hamiltonian, which is the physical effect that makes adaptive measurement
    basis selection meaningful.
    """
    # Diagonalize: H = V @ diag(eigvals) @ V†
    eigvals, V = jnp.linalg.eigh(H)

    # Time evolution operator in eigenbasis
    phases = jnp.exp(-1j * eigvals * tau)
    # U = V @ diag(phases) @ V†
    U = V @ jnp.diag(phases) @ V.conj().T

    # Evolve density matrix
    rho_t = U @ rho0 @ U.conj().T

    # Singlet probability
    p_s = jnp.real(jnp.trace(P_S @ rho_t))

    # Clip to [0, 1] (numerical safety)
    return jnp.clip(p_s, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Single-seed simulation — will be JIT-compiled and vmapped
# ---------------------------------------------------------------------------

def run_single_seed(key, feedback_params, spin_ops_tuple, constants, n_events):
    """Run one seed of the measurement-basis-selection feedback loop.

    Args:
        key: JAX PRNGKey
        feedback_params: length-15 array [delta_S(6), delta_T(6), alpha, beta, gamma]
        spin_ops_tuple: tuple of (P_S, rho0, S1x_INx, S1y_INy, S1z_INz, S1S2,
                         S1z_plus_S2z, S1x_plus_S2x) — using tuple for vmap compatibility
        constants: tuple of (a_base_rad, J_base_rad, omega_z, tau)
        n_events: int, number of events (static)

    Returns:
        theta_final: (6,) final conformation vector
        mean_p_s: scalar, mean singlet probability across events
    """
    delta_S = feedback_params[:6]
    delta_T = feedback_params[6:12]
    alpha = feedback_params[12]
    beta = feedback_params[13]
    gamma = feedback_params[14]

    (P_S, rho0, S1x_INx, S1y_INy, S1z_INz, S1S2,
     S1z_plus_S2z, S1x_plus_S2x) = spin_ops_tuple

    a_base_rad, J_base_rad, omega_z, tau = constants

    # Pack spin_ops for Hamiltonian builder
    spin_ops_dict = {
        'S1x_INx': S1x_INx,
        'S1y_INy': S1y_INy,
        'S1z_INz': S1z_INz,
        'S1S2': S1S2,
        'S1z_plus_S2z': S1z_plus_S2z,
        'S1x_plus_S2x': S1x_plus_S2x,
    }

    theta = jnp.zeros(6)

    def body_fn(carry, _):
        theta, key = carry

        # Map theta to Hamiltonian parameters
        # a_N in MHz, convert to rad/us: 2*pi*a_N_MHz
        a_N_MHz = A_BASE + alpha * theta[0]
        a_N_rad = 2.0 * jnp.pi * a_N_MHz
        J_MHz = J_BASE + beta * theta[1]
        J_rad = 2.0 * jnp.pi * J_MHz
        phi = gamma * theta[2]

        # Build Hamiltonian
        H = build_hamiltonian_jax(a_N_rad, J_rad, phi, omega_z, spin_ops_dict)

        # Compute singlet probability
        p_s = compute_singlet_prob_jax(H, P_S, rho0, tau)

        # Stochastic measurement outcome
        key, subkey = jax.random.split(key)
        is_singlet = jax.random.uniform(subkey) < p_s

        # Update theta
        theta = theta + jnp.where(is_singlet, delta_S, delta_T)

        return (theta, key), p_s

    (theta_final, _), singlet_probs = jax.lax.scan(
        body_fn, (theta, key), jnp.arange(n_events)
    )

    return theta_final, jnp.mean(singlet_probs)


def run_single_seed_fixed(key, feedback_params, p_s_fixed, n_events):
    """Fixed basis: P_S is constant (no adaptive feedback into Hamiltonian).

    Still uses the evolved delta_S/delta_T for conformational shifts.
    """
    delta_S = feedback_params[:6]
    delta_T = feedback_params[6:12]

    theta = jnp.zeros(6)

    def body_fn(carry, _):
        theta, key = carry
        key, subkey = jax.random.split(key)
        is_singlet = jax.random.uniform(subkey) < p_s_fixed
        theta = theta + jnp.where(is_singlet, delta_S, delta_T)
        return (theta, key), p_s_fixed

    (theta_final, _), _ = jax.lax.scan(
        body_fn, (theta, key), jnp.arange(n_events)
    )

    return theta_final, p_s_fixed


def run_single_seed_classical(key, feedback_params, n_events):
    """Classical: P_S fixed at 0.5 (fair coin flip)."""
    delta_S = feedback_params[:6]
    delta_T = feedback_params[6:12]

    theta = jnp.zeros(6)

    def body_fn(carry, _):
        theta, key = carry
        key, subkey = jax.random.split(key)
        is_singlet = jax.random.uniform(subkey) < 0.5
        theta = theta + jnp.where(is_singlet, delta_S, delta_T)
        return (theta, key), 0.5

    (theta_final, _), _ = jax.lax.scan(
        body_fn, (theta, key), jnp.arange(n_events)
    )

    return theta_final, 0.5


# ---------------------------------------------------------------------------
# Batch runners using vmap
# ---------------------------------------------------------------------------

def make_spin_ops_tuple(spin_ops):
    """Extract spin operators into a tuple for passing to JIT/vmap."""
    return (
        spin_ops['P_S'],
        spin_ops['rho0'],
        spin_ops['S1x_INx'],
        spin_ops['S1y_INy'],
        spin_ops['S1z_INz'],
        spin_ops['S1S2'],
        spin_ops['S1z_plus_S2z'],
        spin_ops['S1x_plus_S2x'],
    )


def make_constants_tuple():
    """Pack physical constants into a tuple."""
    a_base_rad = 2.0 * np.pi * A_BASE
    J_base_rad = 2.0 * np.pi * J_BASE
    return (a_base_rad, J_base_rad, OMEGA_Z, TAU)


def create_batch_runners(spin_ops, n_events):
    """Create JIT-compiled, vmapped batch runner functions.

    Must be called with a specific n_events since it's a static argument
    for jax.lax.scan.
    """
    ops_tuple = make_spin_ops_tuple(spin_ops)
    consts = make_constants_tuple()

    # JIT the single-seed function with static n_events
    @jax.jit
    def run_adaptive_batch(keys, feedback_params):
        """Run adaptive simulation for all seeds in parallel."""
        def single(key):
            return run_single_seed(key, feedback_params, ops_tuple, consts, n_events)
        thetas, mean_ps = jax.vmap(single)(keys)
        return thetas, mean_ps

    # Compute fixed-basis P_S once
    a_base_rad = 2.0 * np.pi * A_BASE
    J_base_rad = 2.0 * np.pi * J_BASE
    H_fixed = build_hamiltonian_jax(
        a_base_rad, J_base_rad, 0.0, OMEGA_Z,
        {k: spin_ops[k] for k in ['S1x_INx', 'S1y_INy', 'S1z_INz',
                                    'S1S2', 'S1z_plus_S2z', 'S1x_plus_S2x']}
    )
    p_s_fixed = compute_singlet_prob_jax(H_fixed, spin_ops['P_S'], spin_ops['rho0'], TAU)
    p_s_fixed_val = float(p_s_fixed)

    @jax.jit
    def run_fixed_batch(keys, feedback_params):
        """Run fixed-basis simulation for all seeds in parallel."""
        def single(key):
            return run_single_seed_fixed(key, feedback_params, p_s_fixed, n_events)
        thetas, mean_ps = jax.vmap(single)(keys)
        return thetas, mean_ps

    @jax.jit
    def run_classical_batch(keys, feedback_params):
        """Run classical simulation for all seeds in parallel."""
        def single(key):
            return run_single_seed_classical(key, feedback_params, n_events)
        thetas, mean_ps = jax.vmap(single)(keys)
        return thetas, mean_ps

    return run_adaptive_batch, run_fixed_batch, run_classical_batch, p_s_fixed_val


# ---------------------------------------------------------------------------
# GA fitness function
# ---------------------------------------------------------------------------

def make_fitness_function(run_adaptive_batch, target, n_seeds):
    """Create the fitness function for differential_evolution.

    Returns a Python function that takes a numpy array and returns a float.
    """
    target_jax = jnp.array(target)
    # Pre-generate keys
    keys = jax.random.split(jax.random.PRNGKey(42), n_seeds)

    def fitness(params_flat):
        feedback_params = jnp.array(params_flat)
        thetas_final, _ = run_adaptive_batch(keys, feedback_params)
        # Block until computation is done (needed for scipy)
        distances = jnp.linalg.norm(thetas_final - target_jax, axis=1)
        mean_dist_sq = float(jnp.mean(distances ** 2))
        return mean_dist_sq  # minimize mean squared distance

    return fitness


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("  DIRECTED NAVIGATION VIA EVOLVED MEASUREMENT-BASIS FEEDBACK")
    print("  JAX-Accelerated Version")
    print("=" * 78)

    initial_distance = np.linalg.norm(THETA_TARGET)

    print(f"\n--- Configuration ---")
    print(f"  JAX platform  : {_PLATFORM}")
    print(f"  JAX devices   : {jax.devices()}")
    print(f"  Target        : theta_target = {THETA_TARGET}")
    print(f"  Initial dist  : ||theta_0 - theta_target|| = {initial_distance:.4f}")
    print(f"  B_field       : {B_FIELD*1e6:.0f} uT")
    print(f"  omega_z       : {OMEGA_Z:.4f} rad/us")
    print(f"  a_base        : {A_BASE} MHz")
    print(f"  J_base        : {J_BASE} MHz")
    print(f"  k_S           : {K_S} us^-1")
    print(f"  k_T           : {K_T} us^-1")
    print(f"  T2            : {T2} us")
    print(f"  tau           : {TAU} us")
    print(f"  N_events GA   : {N_EVENTS_GA}")
    print(f"  N_seeds GA    : {N_SEEDS_GA}")
    print(f"  GA maxiter    : {GA_MAXITER}")
    print(f"  GA popsize    : {GA_POPSIZE}")
    print(f"  N_events comp : {N_EVENTS_COMP}")
    print(f"  N_runs comp   : {N_RUNS_COMP}")

    # ---- Build spin operators ----
    print("\nBuilding spin operators...", flush=True)
    spin_ops = build_spin_operators()

    # ---- Create batch runners (triggers JIT compilation) ----
    print("Creating JIT-compiled batch runners...", flush=True)
    t_jit_start = time.time()

    run_adaptive_batch, run_fixed_batch, run_classical_batch, p_s_fixed = \
        create_batch_runners(spin_ops, N_EVENTS_GA)

    print(f"  P_S(fixed basis) = {p_s_fixed:.6f}")

    # Warm up JIT by running once
    print("Warming up JIT compilation (first run triggers tracing)...", flush=True)
    warmup_keys = jax.random.split(jax.random.PRNGKey(0), N_SEEDS_GA)
    warmup_params = jnp.zeros(15)
    warmup_result = run_adaptive_batch(warmup_keys, warmup_params)
    warmup_result[0].block_until_ready()

    t_jit = time.time() - t_jit_start
    print(f"  JIT warmup completed in {t_jit:.1f}s")

    # ===================================================================
    # PHASE 1: EVOLUTIONARY OPTIMIZATION
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 1: EVOLUTIONARY OPTIMIZATION")
    print(f"  differential_evolution: maxiter={GA_MAXITER}, popsize={GA_POPSIZE}")
    print(f"  Each evaluation: {N_SEEDS_GA} seeds x {N_EVENTS_GA} events (JIT+vmap)")
    print(f"{'='*78}\n")

    fitness_fn = make_fitness_function(run_adaptive_batch, THETA_TARGET, N_SEEDS_GA)

    generation_log = []
    gen_counter = [0]
    best_fun = [float('inf')]
    eval_counter = [0]
    t_ga_start = time.time()

    def ga_callback(xk, convergence):
        gen_counter[0] += 1
        current_fun = fitness_fn(xk)
        if current_fun < best_fun[0]:
            best_fun[0] = current_fun
        mean_dist = np.sqrt(best_fun[0])
        elapsed = time.time() - t_ga_start
        generation_log.append({
            'gen': gen_counter[0],
            'mean_dist': mean_dist,
            'mean_dist_sq': best_fun[0],
            'elapsed': elapsed,
        })
        print(f"  Gen {gen_counter[0]:>3d} | Best RMS dist: {mean_dist:>8.4f} | "
              f"Dist^2: {best_fun[0]:>10.4f} | "
              f"Conv: {convergence:.4f} | "
              f"Elapsed: {elapsed:.1f}s", flush=True)

    result = differential_evolution(
        fitness_fn,
        bounds=BOUNDS,
        maxiter=GA_MAXITER,
        popsize=GA_POPSIZE,
        seed=GA_SEED,
        callback=ga_callback,
        tol=1e-6,
        mutation=(0.5, 1.0),
        recombination=0.7,
        disp=False,
    )

    t_ga = time.time() - t_ga_start

    # Decode optimized parameters
    opt_x = result.x
    opt_delta_S = opt_x[0:6]
    opt_delta_T = opt_x[6:12]
    opt_alpha = opt_x[12]
    opt_beta = opt_x[13]
    opt_gamma = opt_x[14]

    print(f"\n--- GA Results ---")
    print(f"  Optimization time : {t_ga:.1f}s")
    print(f"  GA converged      : {result.success}")
    print(f"  GA message        : {result.message}")
    print(f"  Best dist^2       : {result.fun:.4f}")
    print(f"  Best RMS dist     : {np.sqrt(result.fun):.4f}")
    print(f"\n  Optimized parameters:")
    print(f"    delta_S = [{', '.join(f'{v:+.4f}' for v in opt_delta_S)}]")
    print(f"    delta_T = [{', '.join(f'{v:+.4f}' for v in opt_delta_T)}]")
    print(f"    alpha   = {opt_alpha:.4f} MHz")
    print(f"    beta    = {opt_beta:.4f} MHz")
    print(f"    gamma   = {opt_gamma:.4f} rad")

    # ===================================================================
    # PHASE 2: COMPARISON OF FOUR CONDITIONS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 2: COMPARISON OF FOUR CONDITIONS")
    print(f"  {N_RUNS_COMP} runs x {N_EVENTS_COMP} events per condition")
    print(f"{'='*78}")

    # Rebuild batch runners for comparison event count if different
    if N_EVENTS_COMP != N_EVENTS_GA:
        print("\n  Recompiling batch runners for comparison event count...", flush=True)
        run_adaptive_batch_comp, run_fixed_batch_comp, run_classical_batch_comp, _ = \
            create_batch_runners(spin_ops, N_EVENTS_COMP)
        # Warmup
        warmup_result = run_adaptive_batch_comp(warmup_keys, warmup_params)
        warmup_result[0].block_until_ready()
        print("  Done.")
    else:
        run_adaptive_batch_comp = run_adaptive_batch
        run_fixed_batch_comp = run_fixed_batch
        run_classical_batch_comp = run_classical_batch

    opt_params_jax = jnp.array(opt_x)

    # Generate random feedback parameters for Condition 4
    rng_rand = np.random.default_rng(seed=999)
    rand_params = np.zeros(15)
    rand_params[:6] = rng_rand.uniform(-0.3, 0.3, size=6)
    rand_params[6:12] = rng_rand.uniform(-0.3, 0.3, size=6)
    rand_params[12] = rng_rand.uniform(0.0, 5.0)
    rand_params[13] = rng_rand.uniform(0.0, 3.0)
    rand_params[14] = rng_rand.uniform(0.0, 0.5)
    rand_params_jax = jnp.array(rand_params)

    # Run comparisons in batches
    # For 200 seeds, run as a single vmap batch
    all_keys = jax.random.split(jax.random.PRNGKey(2000), N_RUNS_COMP)

    # --- CONDITION 1: Adaptive + evolved ---
    print(f"\n  Condition 1: Adaptive + evolved feedback...", flush=True)
    t0 = time.time()
    finals_1, mean_ps_1 = run_adaptive_batch_comp(all_keys, opt_params_jax)
    finals_1.block_until_ready()
    t1 = time.time() - t0
    print(f"    Done in {t1:.2f}s  (mean P_S = {float(jnp.mean(mean_ps_1)):.4f})")

    # --- CONDITION 2: Fixed basis + evolved ---
    print(f"\n  Condition 2: Fixed basis + evolved feedback...", flush=True)
    t0 = time.time()
    finals_2, _ = run_fixed_batch_comp(all_keys, opt_params_jax)
    finals_2.block_until_ready()
    t2 = time.time() - t0
    print(f"    Done in {t2:.2f}s  (P_S fixed = {p_s_fixed:.4f})")

    # --- CONDITION 3: Classical + evolved ---
    print(f"\n  Condition 3: Classical + evolved feedback (P_S=0.5)...", flush=True)
    t0 = time.time()
    finals_3, _ = run_classical_batch_comp(all_keys, opt_params_jax)
    finals_3.block_until_ready()
    t3 = time.time() - t0
    print(f"    Done in {t3:.2f}s")

    # --- CONDITION 4: Adaptive + random ---
    print(f"\n  Condition 4: Adaptive + random feedback...", flush=True)
    t0 = time.time()
    finals_4, mean_ps_4 = run_adaptive_batch_comp(all_keys, rand_params_jax)
    finals_4.block_until_ready()
    t4 = time.time() - t0
    print(f"    Done in {t4:.2f}s  (mean P_S = {float(jnp.mean(mean_ps_4)):.4f})")

    # Convert to numpy for analysis
    finals_1_np = np.array(finals_1)
    finals_2_np = np.array(finals_2)
    finals_3_np = np.array(finals_3)
    finals_4_np = np.array(finals_4)

    # ===================================================================
    # PHASE 3: METRICS AND COMPARISON
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 3: METRICS AND COMPARISON")
    print(f"{'='*78}")

    threshold = 0.20 * initial_distance

    print(f"\n  Target: {THETA_TARGET}")
    print(f"  Initial distance: {initial_distance:.4f}")
    print(f"  Hitting threshold (20% of initial): {threshold:.4f}")

    conditions = {
        'Adaptive + evolved': finals_1_np,
        'Fixed basis + evolved': finals_2_np,
        'Classical + evolved': finals_3_np,
        'Adaptive + random': finals_4_np,
    }

    results_table = {}

    for name, finals in conditions.items():
        dists = np.linalg.norm(finals - THETA_TARGET, axis=1)
        mean_dist = np.mean(dists)
        std_dist = np.std(dists)
        hitting_rate = np.mean(dists < threshold)
        mean_fitness = np.mean(-(dists ** 2))
        results_table[name] = {
            'mean_dist': mean_dist,
            'std_dist': std_dist,
            'hitting_rate': hitting_rate,
            'mean_fitness': mean_fitness,
        }

    # Print comparison table
    print(f"\n  {'Condition':<25s} | {'Mean dist':>10s} | {'Std':>8s} | "
          f"{'Hit rate':>9s} | {'Mean fitness':>13s}")
    print(f"  {'-'*25}-+-{'-'*10}-+-{'-'*8}-+-{'-'*9}-+-{'-'*13}")

    for name in ['Adaptive + evolved', 'Fixed basis + evolved',
                 'Classical + evolved', 'Adaptive + random']:
        r = results_table[name]
        print(f"  {name:<25s} | {r['mean_dist']:>10.4f} | {r['std_dist']:>8.4f} | "
              f"{r['hitting_rate']:>9.1%} | {r['mean_fitness']:>13.4f}")

    # ===================================================================
    # PHASE 4: STATISTICAL SIGNIFICANCE
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 4: STATISTICAL SIGNIFICANCE")
    print(f"{'='*78}")

    from scipy import stats

    dists_1 = np.linalg.norm(finals_1_np - THETA_TARGET, axis=1)
    dists_2 = np.linalg.norm(finals_2_np - THETA_TARGET, axis=1)
    dists_3 = np.linalg.norm(finals_3_np - THETA_TARGET, axis=1)
    dists_4 = np.linalg.norm(finals_4_np - THETA_TARGET, axis=1)

    comparisons = [
        ("Adaptive+evolved vs Fixed+evolved", dists_1, dists_2),
        ("Adaptive+evolved vs Classical+evolved", dists_1, dists_3),
        ("Adaptive+evolved vs Adaptive+random", dists_1, dists_4),
        ("Fixed+evolved vs Classical+evolved", dists_2, dists_3),
    ]

    print(f"\n  Two-sample t-tests on distance to target:")
    for label, d_a, d_b in comparisons:
        t_stat, p_val = stats.ttest_ind(d_a, d_b)
        pooled_std = np.sqrt((np.std(d_a)**2 + np.std(d_b)**2) / 2)
        cohens_d = (np.mean(d_a) - np.mean(d_b)) / pooled_std if pooled_std > 1e-12 else 0.0
        print(f"    {label}")
        print(f"      t = {t_stat:+.4f}, p = {p_val:.2e}, Cohen's d = {cohens_d:+.4f}")

    print(f"\n  Mann-Whitney U tests on distance to target:")
    for label, d_a, d_b in comparisons:
        u_stat, p_val = stats.mannwhitneyu(d_a, d_b, alternative='two-sided')
        print(f"    {label}")
        print(f"      U = {u_stat:.1f}, p = {p_val:.2e}")

    # ===================================================================
    # PHASE 5: DETAILED ANALYSIS
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  PHASE 5: DETAILED ANALYSIS")
    print(f"{'='*78}")

    # Mean final theta for each condition
    print(f"\n  Mean final theta vectors:")
    for name, finals in conditions.items():
        mean_theta = np.mean(finals, axis=0)
        print(f"    {name:<25s}: [{', '.join(f'{v:+.4f}' for v in mean_theta)}]")
    print(f"    {'Target':<25s}: [{', '.join(f'{v:+.4f}' for v in THETA_TARGET)}]")

    # Per-dimension analysis
    print(f"\n  Per-dimension mean distance from target:")
    print(f"    {'Dim':>4s}  {'Target':>7s}  {'Adpt+Evo':>9s}  {'Fix+Evo':>9s}  "
          f"{'Cls+Evo':>9s}  {'Adpt+Rnd':>9s}")
    for d in range(6):
        t_val = THETA_TARGET[d]
        m1 = np.mean(finals_1_np[:, d]) - t_val
        m2 = np.mean(finals_2_np[:, d]) - t_val
        m3 = np.mean(finals_3_np[:, d]) - t_val
        m4 = np.mean(finals_4_np[:, d]) - t_val
        print(f"    {d:>4d}  {t_val:>+7.2f}  {m1:>+9.4f}  {m2:>+9.4f}  "
              f"{m3:>+9.4f}  {m4:>+9.4f}")

    # GA convergence summary
    if generation_log:
        print(f"\n  GA convergence summary:")
        print(f"    {'Gen':>4s}  {'RMS dist':>10s}  {'Dist^2':>10s}  {'Elapsed':>8s}")
        for entry in generation_log:
            print(f"    {entry['gen']:>4d}  {entry['mean_dist']:>10.4f}  "
                  f"{entry['mean_dist_sq']:>10.4f}  {entry['elapsed']:>7.1f}s")

    # ===================================================================
    # VERDICT
    # ===================================================================
    print(f"\n{'='*78}")
    print(f"  VERDICT")
    print(f"{'='*78}")

    r1 = results_table['Adaptive + evolved']
    r2 = results_table['Fixed basis + evolved']
    r3 = results_table['Classical + evolved']
    r4 = results_table['Adaptive + random']

    # Check if Adaptive+evolved is best
    adaptive_best = (r1['mean_dist'] < r2['mean_dist'] and
                     r1['mean_dist'] < r3['mean_dist'] and
                     r1['mean_dist'] < r4['mean_dist'])

    t_12, p_12 = stats.ttest_ind(dists_1, dists_2)
    t_13, p_13 = stats.ttest_ind(dists_1, dists_3)
    t_14, p_14 = stats.ttest_ind(dists_1, dists_4)

    sig_vs_fixed = p_12 < 0.05 and r1['mean_dist'] < r2['mean_dist']
    sig_vs_classical = p_13 < 0.05 and r1['mean_dist'] < r3['mean_dist']
    sig_vs_random = p_14 < 0.05 and r1['mean_dist'] < r4['mean_dist']

    print(f"\n  Distance improvement (lower = better):")
    print(f"    Initial distance to target:     {initial_distance:.4f}")
    print(f"    Adaptive + evolved:             {r1['mean_dist']:.4f} "
          f"({(1 - r1['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Fixed basis + evolved:          {r2['mean_dist']:.4f} "
          f"({(1 - r2['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Classical + evolved:            {r3['mean_dist']:.4f} "
          f"({(1 - r3['mean_dist']/initial_distance)*100:+.1f}%)")
    print(f"    Adaptive + random:              {r4['mean_dist']:.4f} "
          f"({(1 - r4['mean_dist']/initial_distance)*100:+.1f}%)")

    print(f"\n  Significance (Adaptive+evolved vs each):")
    print(f"    vs Fixed basis:  p = {p_12:.2e}  {'SIGNIFICANT' if sig_vs_fixed else 'not significant'}")
    print(f"    vs Classical:    p = {p_13:.2e}  {'SIGNIFICANT' if sig_vs_classical else 'not significant'}")
    print(f"    vs Random fbk:  p = {p_14:.2e}  {'SIGNIFICANT' if sig_vs_random else 'not significant'}")

    # Overall verdict
    if adaptive_best and sig_vs_fixed and sig_vs_classical and sig_vs_random:
        print(f"\n  >>> STRONG POSITIVE RESULT <<<")
        print(f"  Evolution CAN tune the adaptive measurement-basis feedback loop")
        print(f"  for directed navigation toward a specific target.")
        print(f"  Adaptive + evolved is SIGNIFICANTLY closer to target than ALL")
        print(f"  three control conditions.")
        print(f"\n  This means:")
        print(f"    1. Adaptive measurement (choosing which questions to ask) matters")
        print(f"       -- fixed basis with same feedback is worse.")
        print(f"    2. Quantum dynamics matter -- classical coin flip is worse.")
        print(f"    3. Evolutionary tuning matters -- random feedback is worse.")
        print(f"  ALL THREE components (adaptation + quantum + evolution) contribute")
        print(f"  to goal-directed navigation in conformation space.")
    elif adaptive_best and (sig_vs_fixed or sig_vs_classical or sig_vs_random):
        print(f"\n  >>> PARTIAL POSITIVE RESULT <<<")
        print(f"  Adaptive + evolved achieves the BEST mean distance to target,")
        print(f"  with significant advantage over at least one control condition.")
        factors = []
        if sig_vs_fixed:
            factors.append("measurement-basis adaptation")
        if sig_vs_classical:
            factors.append("quantum dynamics")
        if sig_vs_random:
            factors.append("evolutionary parameter tuning")
        print(f"  Significant factors: {', '.join(factors)}")
        if not sig_vs_fixed:
            print(f"  Note: Fixed basis performs comparably, suggesting the evolved")
            print(f"  shift vectors alone may be sufficient without adaptive feedback.")
        if not sig_vs_classical:
            print(f"  Note: Classical performs comparably, suggesting quantum dynamics")
            print(f"  may not be critical for this navigation task.")
        if not sig_vs_random:
            print(f"  Note: Random feedback performs comparably, suggesting the adaptive")
            print(f"  loop alone provides most of the benefit.")
    else:
        print(f"\n  >>> NEGATIVE OR INCONCLUSIVE RESULT <<<")
        print(f"  Adaptive + evolved does NOT clearly outperform all controls.")
        if r2['mean_dist'] <= r1['mean_dist']:
            print(f"  Fixed basis matches/beats adaptive, suggesting adaptation is")
            print(f"  not necessary -- evolved shift vectors alone suffice.")
        if r3['mean_dist'] <= r1['mean_dist']:
            print(f"  Classical matches/beats adaptive, suggesting quantum dynamics")
            print(f"  are not needed for this type of navigation.")
        if r4['mean_dist'] <= r1['mean_dist']:
            print(f"  Random feedback matches/beats evolved, suggesting evolution")
            print(f"  does not improve navigation performance.")

    total_time = time.time() - t_ga_start + t_jit
    print(f"\n  Total wall-clock time: {total_time:.1f}s "
          f"(JIT: {t_jit:.1f}s, GA: {t_ga:.1f}s, "
          f"Comparison: {t1+t2+t3+t4:.1f}s)")

    print(f"\n{'='*78}\n")


if __name__ == "__main__":
    main()
