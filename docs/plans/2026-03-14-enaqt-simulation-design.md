# ENAQT Simulation for Microtubule Chromophore Networks

## Date: 2026-03-14

## Purpose

Determine whether quantum effects in the microtubule tryptophan chromophore network produce a measurable, systematic bias in the probability distribution over conformational states at physiological dephasing rates (γ/κ ≈ 0.01–0.1), compared to the fully classical limit. This is the decisive calculation for NFT's Level B claim.

## Success Criteria

- **Phase 1 (existence)**: The steady-state probability distribution at physiological γ/κ is measurably different from the classical limit, and the difference is non-monotonic (peaks at an intermediate γ/κ).
- **Phase 2 (directionality)**: Transport efficiency to a sink site peaks at intermediate γ/κ — the ENAQT signature — demonstrating directional quantum advantage.
- **Phase 3 (evolvability)**: A genetic algorithm over geometry parameters finds configurations that maximize directional transport efficiency at physiological γ/κ, demonstrating that natural selection could discover quantum-advantageous microtubule geometries.

## Approach

Extend the existing `anti_zeno_chromophore_test.py` codebase. Pure numpy/scipy, no new dependencies.

## Physics

### System Hamiltonian

H = H_walk + H_pot

- H_walk = γ * C, where C is the dipole-dipole coupling matrix from the helix geometry model (already implemented)
- H_pot = diag(E_1, ..., E_N), static site energies from disorder (already implemented)
- γ is the coherent hopping rate, the sweep variable

### Open-system dynamics

Lindblad master equation:

ρ̇ = -i[H, ρ] + Σ_j (L_j ρ L_j† - ½{L_j†L_j, ρ})

Local dephasing operators: L_j = √κ Z_j where Z_j = |j⟩⟨j| (projector onto site j)

κ is the dephasing rate, derived from spectral density at the reference excitonic gap (already implemented).

### Phase 1: Quantum Bias Measurement

For each γ/κ value in a logarithmic sweep from 10⁻⁴ to 10:

1. Build H(γ) = γ * C + H_pot (scale the coupling matrix by γ, keep H_pot fixed)
2. Build the Liouvillian superoperator L(γ, κ)
3. Find steady state ρ_ss by solving L vec(ρ) = 0 (smallest singular value of L)
4. Extract site populations p_i = ρ_ss[i,i]
5. Compute classical reference: the steady state at γ/κ = 10⁻⁴ (effectively zero coherence)
6. Compute quantum bias metrics:
   - Trace distance: D(p, p_classical) = ½ Σ|p_i - p_classical_i|
   - Off-diagonal coherence: C = Σ_{i≠j} |ρ_ss[i,j]|
   - Entropy difference: ΔS = S(p) - S(p_classical) where S = -Σ p_i log p_i

Output: quantum bias vs. γ/κ curve. Non-zero bias at physiological γ/κ ≈ 0.01-0.1 with a peak proves Phase 1.

### Phase 2: Transport Efficiency (ENAQT)

Add a sink on site N:

L_sink = √Γ_sink |ground⟩⟨N|

In the single-excitation subspace, this is an additional Lindblad operator that irreversibly removes population from site N. The sink rate Γ_sink is a parameter (typically set to match the excitonic coupling scale).

Protocol:
1. Initialize ρ(0) = |1⟩⟨1| (excitation on site 1)
2. Evolve under the master equation (with sink) for time T_max
3. Transport efficiency η = 1 - Tr(ρ(T_max)) (total population lost to sink)
4. Sweep γ/κ, plot η vs. γ/κ
5. ENAQT signature: η peaks at intermediate γ/κ

Implementation: time-evolve using matrix exponential of Liouvillian (existing approach), sample at time steps, integrate sink capture.

### Phase 3: Evolutionary Geometry Search

Parameterize the helix geometry by a vector:

θ = [helix_radius_nm, helix_rise_nm, helix_twist_deg, dipole_tilt_deg, disorder_cm, coupling_cm]

with bounds:
- helix_radius_nm: [1.0, 4.0] (microtubule radius range)
- helix_rise_nm: [0.4, 1.5]
- helix_twist_deg: [20.0, 40.0] (around the 27.7° for 13-pf)
- dipole_tilt_deg: [0.0, 45.0]
- disorder_cm: [0.0, 100.0]
- coupling_cm: [20.0, 120.0]

Objective: maximize η at physiological κ (fixed from spectral density at 310K).

Method: scipy.optimize.differential_evolution (population-based global optimizer, no gradient needed).

Output: optimized geometry parameters and their η vs. the default helix geometry's η. If η_optimized >> η_default, evolution had room to optimize. If η_default is already near-optimal, the 13-pf geometry may be pre-adapted.

## Code Architecture

```
enaqt_simulation/
├── __init__.py
├── hamiltonian.py        # Reuse/adapt helix geometry builder from anti_zeno code
├── lindblad.py           # Liouvillian construction, steady-state solver
├── transport.py          # Sink dynamics, transport efficiency calculation
├── sweep.py              # γ/κ sweep logic, bias metrics
├── evolve.py             # GA/differential evolution over geometry
├── cli.py                # Command-line interface for all three phases
└── results/              # CSV output directory
```

Key reuse from anti_zeno_chromophore_test.py:
- build_helix_model() → hamiltonian.py
- liouvillian_local_dephasing() → lindblad.py
- spectral_density_ps_inv(), kappa_from_spectral_density() → lindblad.py
- Unit conversion functions → shared utils

## Default Parameters

From the paper draft and existing code:
- sites: 8
- coupling_cm: 60.0 (Babcock et al. 2024)
- disorder_cm: 25.0
- helix_radius_nm: 2.0
- helix_rise_nm: 0.8
- helix_twist_deg: 27.7 (13-protofilament geometry)
- dipole_tilt_deg: 20.0
- spectral_density: drude
- bath_strength_cm: 35.0
- cutoff_cm: 53.0
- temperature_k: 310.0 (physiological)
- sink_rate_cm: 1.0 (Phase 2, adjustable)

## Output Format

### Phase 1 CSV
```
gamma_kappa_ratio, gamma_ps_inv, kappa_ps_inv, trace_distance, coherence_sum, entropy_diff, site_0_pop, ..., site_7_pop
```

### Phase 2 CSV
```
gamma_kappa_ratio, gamma_ps_inv, kappa_ps_inv, transport_efficiency, transfer_time_ps
```

### Phase 3 CSV
```
generation, best_fitness, helix_radius, helix_rise, helix_twist, dipole_tilt, disorder, coupling, transport_efficiency
```

## What Would Kill Level B

- Phase 1: If the trace distance between intermediate-γ/κ and classical-limit distributions is < 10⁻⁶ across the entire sweep → no measurable quantum bias → Level B has no substrate effect to work with.
- Phase 2: If η is monotonically decreasing with γ/κ (more coherence = worse transport) → no ENAQT → the intermediate regime is not special.
- Phase 3: If the GA cannot find any geometry with η significantly above the classical baseline → evolution could not have selected for quantum transport → the evolutionary argument fails.

## What Would Support Level B

- Phase 1: Non-zero trace distance at γ/κ ≈ 0.01-0.1, peaking at an intermediate value → quantum effects produce systematic bias even in the strong-dephasing regime.
- Phase 2: η peaks at intermediate γ/κ near the physiological operating point → ENAQT in microtubule geometry → the dephasing regime is optimized, not limiting.
- Phase 3: The default 13-pf-inspired geometry is near the GA optimum → evolution may have already found the quantum-optimal configuration.
