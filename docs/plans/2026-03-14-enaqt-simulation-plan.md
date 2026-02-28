# ENAQT Microtubule Simulation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Determine whether quantum effects in microtubule chromophore networks produce a measurable probability bias at physiological dephasing rates, deciding the fate of NFT Level B.

**Architecture:** Three-phase simulation extending existing anti-Zeno codebase. Phase 1 sweeps γ/κ and measures steady-state distribution bias. Phase 2 adds a sink site and measures ENAQT transport efficiency. Phase 3 uses differential evolution to search geometry space. All phases share a core library extracted from `anti_zeno_chromophore_test.py`.

**Tech Stack:** Python 3.14, numpy 2.4, scipy 1.17. No new dependencies. Venv at `.venv/`.

---

### Task 1: Extract shared library from anti-Zeno code

**Files:**
- Create: `enaqt_simulation/__init__.py`
- Create: `enaqt_simulation/core.py`
- Read: `anti_zeno_chromophore_test.py`

**Step 1: Create package directory**

Run: `mkdir -p enaqt_simulation`

**Step 2: Create `__init__.py`**

```python
```

(empty file)

**Step 3: Create `core.py` with extracted functions**

Extract the following from `anti_zeno_chromophore_test.py` into `enaqt_simulation/core.py`:

```python
"""Shared physics primitives for ENAQT simulation.

Extracted from anti_zeno_chromophore_test.py. All units in rad/ps internally,
cm⁻¹ at the interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np
from scipy.linalg import eigh


CM_TO_RAD_PER_PS = 2.0 * pi * 29.9792458e9 / 1e12
KB_OVER_HBAR_PS_K = 1.380649e-23 / 1.054571817e-34 / 1e12
EPS = 1e-15


@dataclass
class HamiltonianModel:
    hamiltonian: np.ndarray
    coupling_matrix: np.ndarray  # NEW: the pure coupling part (no disorder), unscaled
    site_energies: np.ndarray    # NEW: the diagonal disorder part
    label: str
    nearest_neighbor_median_cm: float
    all_pair_median_cm: float
    all_pair_max_cm: float


def cm_to_rad_ps(value_cm: float) -> float:
    return value_cm * CM_TO_RAD_PER_PS


def rad_ps_to_cm(value_rad_ps: float) -> float:
    return value_rad_ps / CM_TO_RAD_PER_PS


def unit_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm < EPS:
        raise ValueError("Cannot normalize a zero vector.")
    return vector / norm


def summarize_couplings(h: np.ndarray) -> tuple[float, float, float]:
    couplings_cm = np.abs(rad_ps_to_cm(h))
    sites = h.shape[0]
    nearest_neighbor = [couplings_cm[i, i + 1] for i in range(sites - 1)]
    all_pairs = [couplings_cm[i, j] for i in range(sites) for j in range(i + 1, sites)]
    return (
        float(np.median(nearest_neighbor)),
        float(np.median(all_pairs)),
        float(np.max(all_pairs)),
    )


def build_helix_model(
    sites: int,
    coupling_cm: float,
    disorder_cm: float,
    seed: int,
    helix_radius_nm: float,
    helix_rise_nm: float,
    helix_twist_deg: float,
    dipole_tilt_deg: float,
) -> HamiltonianModel:
    rng = np.random.default_rng(seed)

    site_energies = np.zeros(sites, dtype=float)
    if disorder_cm:
        site_energies = rng.normal(0.0, disorder_cm, size=sites)

    h_pot = np.diag(cm_to_rad_ps(site_energies)).astype(np.complex128)

    positions: list[np.ndarray] = []
    dipoles: list[np.ndarray] = []
    twist_rad = np.deg2rad(helix_twist_deg)
    tilt_rad = np.deg2rad(dipole_tilt_deg)

    for index in range(sites):
        angle = index * twist_rad
        positions.append(np.array([
            helix_radius_nm * np.cos(angle),
            helix_radius_nm * np.sin(angle),
            index * helix_rise_nm,
        ]))
        tangent = np.array([-np.sin(angle), np.cos(angle), 0.0])
        axial = np.array([0.0, 0.0, 1.0])
        dipole = np.cos(tilt_rad) * tangent + np.sin(tilt_rad) * axial
        dipoles.append(unit_vector(dipole))

    raw_couplings = np.zeros((sites, sites))
    for i in range(sites):
        for j in range(i + 1, sites):
            displacement = positions[j] - positions[i]
            distance = np.linalg.norm(displacement)
            direction = displacement / distance
            orientation = (np.dot(dipoles[i], dipoles[j])
                           - 3.0 * np.dot(dipoles[i], direction)
                           * np.dot(dipoles[j], direction))
            raw_couplings[i, j] = orientation / (distance ** 3)
            raw_couplings[j, i] = raw_couplings[i, j]

    nearest_neighbor_raw = np.abs(
        np.array([raw_couplings[i, i + 1] for i in range(sites - 1)])
    )
    raw_scale = coupling_cm / max(float(np.median(nearest_neighbor_raw)), EPS)

    # Coupling matrix in rad/ps, UNSCALED by gamma (gamma=1 equivalent)
    coupling_matrix = cm_to_rad_ps(raw_scale * raw_couplings).astype(np.complex128)

    h_full = coupling_matrix + h_pot

    nn_median_cm, all_pair_median_cm, all_pair_max_cm = summarize_couplings(coupling_matrix)
    return HamiltonianModel(
        hamiltonian=h_full,
        coupling_matrix=coupling_matrix,
        site_energies=site_energies,
        label=(
            f"helix (radius={helix_radius_nm} nm, rise={helix_rise_nm} nm, "
            f"twist={helix_twist_deg} deg, tilt={dipole_tilt_deg} deg)"
        ),
        nearest_neighbor_median_cm=nn_median_cm,
        all_pair_median_cm=all_pair_median_cm,
        all_pair_max_cm=all_pair_max_cm,
    )


def reference_gap_ps_inv(h: np.ndarray) -> float:
    eigvals = np.sort(eigh(h, eigvals_only=True).real)
    gaps = np.diff(eigvals)
    positive_gaps = gaps[gaps > 1e-9]
    if positive_gaps.size == 0:
        raise ValueError("No positive excitonic gaps found.")
    return float(np.median(positive_gaps))


def thermal_weight(omega_ps_inv: float, temperature_k: float) -> float:
    x = omega_ps_inv / (2.0 * KB_OVER_HBAR_PS_K * temperature_k)
    if abs(x) < 1e-12:
        return 1.0 / EPS
    return 1.0 / np.tanh(x)


def spectral_density_ps_inv(
    omega_ps_inv: float,
    bath_strength_cm: float,
    cutoff_cm: float,
) -> float:
    if omega_ps_inv <= 0.0:
        return 0.0
    strength = cm_to_rad_ps(bath_strength_cm)
    cutoff = cm_to_rad_ps(cutoff_cm)
    return 2.0 * strength * cutoff * omega_ps_inv / (omega_ps_inv ** 2 + cutoff ** 2)


def derive_kappa(
    omega_ref_ps_inv: float,
    bath_strength_cm: float,
    cutoff_cm: float,
    temperature_k: float,
) -> float:
    j_value = spectral_density_ps_inv(omega_ref_ps_inv, bath_strength_cm, cutoff_cm)
    return 2.0 * pi * j_value * thermal_weight(omega_ref_ps_inv, temperature_k)


def build_liouvillian(h: np.ndarray, kappa_ps_inv: float) -> np.ndarray:
    n = h.shape[0]
    ident = np.eye(n, dtype=np.complex128)
    liouvillian = -1j * (np.kron(ident, h) - np.kron(h.T, ident))

    for i in range(n):
        lop = np.zeros((n, n), dtype=np.complex128)
        lop[i, i] = np.sqrt(kappa_ps_inv)
        ld_l = lop.conj().T @ lop
        liouvillian += np.kron(lop.conj(), lop)
        liouvillian -= 0.5 * np.kron(ident, ld_l)
        liouvillian -= 0.5 * np.kron(ld_l.T, ident)
    return liouvillian


def build_liouvillian_with_sink(
    h: np.ndarray,
    kappa_ps_inv: float,
    sink_site: int,
    sink_rate_ps_inv: float,
) -> np.ndarray:
    liouvillian = build_liouvillian(h, kappa_ps_inv)
    n = h.shape[0]
    ident = np.eye(n, dtype=np.complex128)

    # Sink operator: |ground><sink_site| removes population from sink_site
    # In single-excitation subspace this is just decay from site sink_site
    lop = np.zeros((n, n), dtype=np.complex128)
    lop[sink_site, sink_site] = np.sqrt(sink_rate_ps_inv)
    ld_l = lop.conj().T @ lop
    liouvillian += np.kron(lop.conj(), lop)
    liouvillian -= 0.5 * np.kron(ident, ld_l)
    liouvillian -= 0.5 * np.kron(ld_l.T, ident)
    return liouvillian


def steady_state(liouvillian: np.ndarray, sites: int) -> np.ndarray:
    _, s, vh = np.linalg.svd(liouvillian)
    rho_vec = vh[-1, :].conj()
    rho = rho_vec.reshape((sites, sites), order="F")
    rho = (rho + rho.conj().T) / 2.0
    rho /= np.trace(rho)
    return rho
```

**Step 4: Verify extraction works**

Run: `.venv/bin/python3 -c "from enaqt_simulation.core import build_helix_model, derive_kappa; print('OK')"`

Expected: `OK`

**Step 5: Commit**

```
git add enaqt_simulation/__init__.py enaqt_simulation/core.py
git commit -m "extract shared physics core from anti-Zeno code for ENAQT simulation"
```

---

### Task 2: Implement Phase 1 — Quantum Bias Sweep

**Files:**
- Create: `enaqt_simulation/phase1_bias.py`

**Step 1: Write `phase1_bias.py`**

This is the decisive calculation. Sweeps γ/κ, computes steady-state distributions, measures quantum bias.

```python
"""Phase 1: Does the intermediate-dephasing regime produce a measurable
probability bias compared to the fully classical limit?

Sweeps γ/κ from near-zero to ~10, computes the steady-state density matrix
at each point, and measures divergence from the classical (fully dephased) limit.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from enaqt_simulation.core import (
    HamiltonianModel,
    build_helix_model,
    build_liouvillian,
    cm_to_rad_ps,
    derive_kappa,
    reference_gap_ps_inv,
    steady_state,
)


@dataclass
class BiasRow:
    gamma_kappa_ratio: float
    gamma_ps_inv: float
    kappa_ps_inv: float
    trace_distance: float
    coherence_sum: float
    entropy_diff: float
    populations: list[float]


def site_populations(rho: np.ndarray) -> np.ndarray:
    return np.real(np.diag(rho))


def trace_distance_populations(p: np.ndarray, q: np.ndarray) -> float:
    return 0.5 * float(np.sum(np.abs(p - q)))


def coherence_sum(rho: np.ndarray) -> float:
    n = rho.shape[0]
    total = 0.0
    for i in range(n):
        for j in range(n):
            if i != j:
                total += abs(rho[i, j])
    return total


def shannon_entropy(p: np.ndarray) -> float:
    p_clipped = np.clip(p, 1e-30, None)
    return -float(np.sum(p_clipped * np.log(p_clipped)))


def make_hamiltonian_at_gamma(
    model: HamiltonianModel, gamma: float
) -> np.ndarray:
    h_pot = np.diag(cm_to_rad_ps(model.site_energies)).astype(np.complex128)
    return gamma * model.coupling_matrix + h_pot


def sweep_gamma_kappa(
    model: HamiltonianModel,
    kappa_ps_inv: float,
    gamma_kappa_ratios: np.ndarray,
) -> list[BiasRow]:
    sites = model.hamiltonian.shape[0]

    # Classical reference: γ/κ → 0
    gamma_classical = gamma_kappa_ratios[0] * kappa_ps_inv
    h_classical = make_hamiltonian_at_gamma(model, gamma_classical)
    liouvillian_classical = build_liouvillian(h_classical, kappa_ps_inv)
    rho_classical = steady_state(liouvillian_classical, sites)
    pop_classical = site_populations(rho_classical)
    entropy_classical = shannon_entropy(pop_classical)

    rows: list[BiasRow] = []
    for ratio in gamma_kappa_ratios:
        gamma = ratio * kappa_ps_inv
        h = make_hamiltonian_at_gamma(model, gamma)
        liouvillian = build_liouvillian(h, kappa_ps_inv)
        rho_ss = steady_state(liouvillian, sites)
        pop = site_populations(rho_ss)

        rows.append(BiasRow(
            gamma_kappa_ratio=float(ratio),
            gamma_ps_inv=float(gamma),
            kappa_ps_inv=float(kappa_ps_inv),
            trace_distance=trace_distance_populations(pop, pop_classical),
            coherence_sum=coherence_sum(rho_ss),
            entropy_diff=shannon_entropy(pop) - entropy_classical,
            populations=pop.tolist(),
        ))
    return rows


def write_csv(path: Path, rows: list[BiasRow], sites: int) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        header = [
            "gamma_kappa_ratio", "gamma_ps_inv", "kappa_ps_inv",
            "trace_distance", "coherence_sum", "entropy_diff",
        ] + [f"site_{i}_pop" for i in range(sites)]
        writer.writerow(header)
        for row in rows:
            writer.writerow([
                f"{row.gamma_kappa_ratio:.8g}",
                f"{row.gamma_ps_inv:.8g}",
                f"{row.kappa_ps_inv:.8g}",
                f"{row.trace_distance:.12g}",
                f"{row.coherence_sum:.12g}",
                f"{row.entropy_diff:.12g}",
            ] + [f"{p:.12g}" for p in row.populations])


def print_results(rows: list[BiasRow]) -> None:
    print("Phase 1: Quantum Bias Sweep")
    print("===========================")
    print()
    print(f"{'gamma/kappa':>12} {'trace_dist':>12} {'coherence':>12} {'entropy_d':>12}")
    for row in rows:
        print(
            f"{row.gamma_kappa_ratio:12.6f} "
            f"{row.trace_distance:12.8f} "
            f"{row.coherence_sum:12.8f} "
            f"{row.entropy_diff:12.8f}"
        )

    # Find peak trace distance
    peak_row = max(rows, key=lambda r: r.trace_distance)
    print()
    print(f"Peak trace distance: {peak_row.trace_distance:.8f} at gamma/kappa = {peak_row.gamma_kappa_ratio:.6f}")

    # Check physiological range
    physio_rows = [r for r in rows if 0.005 <= r.gamma_kappa_ratio <= 0.15]
    if physio_rows:
        max_physio = max(physio_rows, key=lambda r: r.trace_distance)
        print(f"Max trace distance in physiological range [0.005, 0.15]: {max_physio.trace_distance:.8f}")

    # Verdict
    if peak_row.trace_distance < 1e-6:
        print()
        print("VERDICT: No measurable quantum bias. Level B is not supported.")
    else:
        # Check non-monotonicity
        peak_idx = rows.index(peak_row)
        if 0 < peak_idx < len(rows) - 1:
            print()
            print("VERDICT: Non-zero quantum bias with non-monotonic peak. ENAQT regime detected.")
            print("Level B has a substrate effect to work with.")
        else:
            print()
            print("VERDICT: Non-zero quantum bias but monotonic (peak at boundary).")
            print("Suggestive but not the ENAQT signature.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Quantum bias sweep over gamma/kappa.")
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--coupling-cm", type=float, default=60.0)
    parser.add_argument("--disorder-cm", type=float, default=25.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--helix-radius-nm", type=float, default=2.0)
    parser.add_argument("--helix-rise-nm", type=float, default=0.8)
    parser.add_argument("--helix-twist-deg", type=float, default=27.7)
    parser.add_argument("--dipole-tilt-deg", type=float, default=20.0)
    parser.add_argument("--bath-strength-cm", type=float, default=35.0)
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument("--ratio-min", type=float, default=1e-4)
    parser.add_argument("--ratio-max", type=float, default=10.0)
    parser.add_argument("--ratio-count", type=int, default=50)
    parser.add_argument("--csv-out", type=Path, default=None)
    args = parser.parse_args()

    model = build_helix_model(
        sites=args.sites,
        coupling_cm=args.coupling_cm,
        disorder_cm=args.disorder_cm,
        seed=args.seed,
        helix_radius_nm=args.helix_radius_nm,
        helix_rise_nm=args.helix_rise_nm,
        helix_twist_deg=args.helix_twist_deg,
        dipole_tilt_deg=args.dipole_tilt_deg,
    )

    omega_ref = reference_gap_ps_inv(model.hamiltonian)
    kappa = derive_kappa(omega_ref, args.bath_strength_cm, args.cutoff_cm, args.temperature_k)

    print(f"kappa (derived)   : {kappa:.6f} ps^-1")
    print(f"reference gap     : {omega_ref:.6f} ps^-1")
    print(f"model             : {model.label}")
    print()

    ratios = np.logspace(np.log10(args.ratio_min), np.log10(args.ratio_max), args.ratio_count)
    rows = sweep_gamma_kappa(model, kappa, ratios)
    print_results(rows)

    if args.csv_out is not None:
        write_csv(args.csv_out, rows, args.sites)
        print(f"\nCSV written to: {args.csv_out}")


if __name__ == "__main__":
    main()
```

**Step 2: Run Phase 1**

Run: `.venv/bin/python3 -m enaqt_simulation.phase1_bias --csv-out results/phase1_bias.csv`

Expected: Table of γ/κ vs. trace distance printed to stdout, CSV written, verdict printed.

**Step 3: Commit**

```
git add enaqt_simulation/phase1_bias.py
git commit -m "implement Phase 1 quantum bias sweep over gamma/kappa"
```

---

### Task 3: Run Phase 1 and evaluate results

**Step 1: Run with default parameters**

Run: `.venv/bin/python3 -m enaqt_simulation.phase1_bias --csv-out results/phase1_bias.csv`

**Step 2: Evaluate**

Read the output. Three possible outcomes:

- **Trace distance > 0 with interior peak** → ENAQT regime exists. Proceed to Phase 2.
- **Trace distance > 0 but monotonic** → Quantum bias exists but no sweet spot. Investigate parameters.
- **Trace distance ≈ 0 everywhere** → No quantum effect at these parameters. Try varying disorder, coupling, or bath parameters before concluding Level B fails.

**Step 3: If outcome is ambiguous, run disorder sweep**

Run with multiple seeds and disorder values to check robustness:
- `--disorder-cm 0.0` (no disorder)
- `--disorder-cm 50.0` (double disorder)
- `--disorder-cm 100.0` (strong disorder)

**Step 4: Commit results**

```
git add results/phase1_bias.csv
git commit -m "Phase 1 results: quantum bias sweep"
```

---

### Task 4: Implement Phase 2 — ENAQT Transport Efficiency

**Files:**
- Create: `enaqt_simulation/phase2_transport.py`

**Step 1: Write `phase2_transport.py`**

```python
"""Phase 2: Does the intermediate-dephasing regime produce directional
transport advantage? The ENAQT test.

Adds a sink site, initializes excitation on site 0, and measures how
efficiently population reaches the sink as a function of gamma/kappa.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from enaqt_simulation.core import (
    HamiltonianModel,
    build_helix_model,
    build_liouvillian_with_sink,
    cm_to_rad_ps,
    derive_kappa,
    reference_gap_ps_inv,
)
from enaqt_simulation.phase1_bias import make_hamiltonian_at_gamma


@dataclass
class TransportRow:
    gamma_kappa_ratio: float
    gamma_ps_inv: float
    kappa_ps_inv: float
    transport_efficiency: float
    mean_transfer_time_ps: float


def compute_transport_efficiency(
    model: HamiltonianModel,
    gamma: float,
    kappa_ps_inv: float,
    sink_site: int,
    sink_rate_ps_inv: float,
    source_site: int,
    t_max_ps: float,
    dt_ps: float,
) -> tuple[float, float]:
    sites = model.hamiltonian.shape[0]
    h = make_hamiltonian_at_gamma(model, gamma)
    liouvillian = build_liouvillian_with_sink(h, kappa_ps_inv, sink_site, sink_rate_ps_inv)

    rho0 = np.zeros((sites, sites), dtype=np.complex128)
    rho0[source_site, source_site] = 1.0
    rho_vec = rho0.reshape(-1, order="F")

    propagator = expm(liouvillian * dt_ps)
    n_steps = int(t_max_ps / dt_ps)

    # Track population loss over time for mean transfer time
    prev_pop = 1.0
    weighted_time = 0.0
    total_captured = 0.0

    for step in range(n_steps):
        rho_vec = propagator @ rho_vec
        rho = rho_vec.reshape((sites, sites), order="F")
        current_pop = float(np.trace(rho).real)
        captured_this_step = prev_pop - current_pop
        if captured_this_step > 0:
            t = (step + 1) * dt_ps
            weighted_time += captured_this_step * t
            total_captured += captured_this_step
        prev_pop = current_pop

    efficiency = total_captured
    mean_time = weighted_time / max(total_captured, 1e-30)
    return efficiency, mean_time


def sweep_transport(
    model: HamiltonianModel,
    kappa_ps_inv: float,
    gamma_kappa_ratios: np.ndarray,
    sink_site: int,
    sink_rate_ps_inv: float,
    source_site: int,
    t_max_ps: float,
    dt_ps: float,
) -> list[TransportRow]:
    rows: list[TransportRow] = []
    for ratio in gamma_kappa_ratios:
        gamma = ratio * kappa_ps_inv
        efficiency, mean_time = compute_transport_efficiency(
            model, gamma, kappa_ps_inv, sink_site, sink_rate_ps_inv,
            source_site, t_max_ps, dt_ps,
        )
        rows.append(TransportRow(
            gamma_kappa_ratio=float(ratio),
            gamma_ps_inv=float(gamma),
            kappa_ps_inv=float(kappa_ps_inv),
            transport_efficiency=efficiency,
            mean_transfer_time_ps=mean_time,
        ))
    return rows


def write_csv(path: Path, rows: list[TransportRow]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "gamma_kappa_ratio", "gamma_ps_inv", "kappa_ps_inv",
            "transport_efficiency", "mean_transfer_time_ps",
        ])
        for row in rows:
            writer.writerow([
                f"{row.gamma_kappa_ratio:.8g}",
                f"{row.gamma_ps_inv:.8g}",
                f"{row.kappa_ps_inv:.8g}",
                f"{row.transport_efficiency:.12g}",
                f"{row.mean_transfer_time_ps:.12g}",
            ])


def print_results(rows: list[TransportRow]) -> None:
    print("Phase 2: Transport Efficiency (ENAQT)")
    print("=====================================")
    print()
    print(f"{'gamma/kappa':>12} {'efficiency':>12} {'mean_t (ps)':>12}")
    for row in rows:
        print(
            f"{row.gamma_kappa_ratio:12.6f} "
            f"{row.transport_efficiency:12.8f} "
            f"{row.mean_transfer_time_ps:12.4f}"
        )

    peak_row = max(rows, key=lambda r: r.transport_efficiency)
    classical_row = rows[0]  # lowest gamma/kappa
    print()
    print(f"Peak efficiency: {peak_row.transport_efficiency:.8f} at gamma/kappa = {peak_row.gamma_kappa_ratio:.6f}")
    print(f"Classical limit: {classical_row.transport_efficiency:.8f} at gamma/kappa = {classical_row.gamma_kappa_ratio:.6f}")
    print(f"Quantum advantage: {peak_row.transport_efficiency - classical_row.transport_efficiency:+.8f}")

    peak_idx = rows.index(peak_row)
    if peak_row.transport_efficiency > classical_row.transport_efficiency and 0 < peak_idx < len(rows) - 1:
        print()
        print("VERDICT: ENAQT signature detected. Transport peaks at intermediate dephasing.")
        print("Quantum probability sculpting produces directional advantage.")
    elif peak_row.transport_efficiency <= classical_row.transport_efficiency:
        print()
        print("VERDICT: No transport advantage from quantum effects.")
    else:
        print()
        print("VERDICT: Transport advantage exists but peaks at boundary. Not classic ENAQT.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: ENAQT transport efficiency sweep.")
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--coupling-cm", type=float, default=60.0)
    parser.add_argument("--disorder-cm", type=float, default=25.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--helix-radius-nm", type=float, default=2.0)
    parser.add_argument("--helix-rise-nm", type=float, default=0.8)
    parser.add_argument("--helix-twist-deg", type=float, default=27.7)
    parser.add_argument("--dipole-tilt-deg", type=float, default=20.0)
    parser.add_argument("--bath-strength-cm", type=float, default=35.0)
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument("--sink-site", type=int, default=-1, help="-1 means last site")
    parser.add_argument("--sink-rate-cm", type=float, default=1.0)
    parser.add_argument("--source-site", type=int, default=0)
    parser.add_argument("--t-max-ps", type=float, default=20.0)
    parser.add_argument("--dt-ps", type=float, default=0.01)
    parser.add_argument("--ratio-min", type=float, default=1e-4)
    parser.add_argument("--ratio-max", type=float, default=10.0)
    parser.add_argument("--ratio-count", type=int, default=40)
    parser.add_argument("--csv-out", type=Path, default=None)
    args = parser.parse_args()

    sink_site = args.sink_site if args.sink_site >= 0 else args.sites - 1

    model = build_helix_model(
        sites=args.sites, coupling_cm=args.coupling_cm, disorder_cm=args.disorder_cm,
        seed=args.seed, helix_radius_nm=args.helix_radius_nm,
        helix_rise_nm=args.helix_rise_nm, helix_twist_deg=args.helix_twist_deg,
        dipole_tilt_deg=args.dipole_tilt_deg,
    )

    omega_ref = reference_gap_ps_inv(model.hamiltonian)
    kappa = derive_kappa(omega_ref, args.bath_strength_cm, args.cutoff_cm, args.temperature_k)
    sink_rate = cm_to_rad_ps(args.sink_rate_cm)

    print(f"kappa (derived)   : {kappa:.6f} ps^-1")
    print(f"sink_rate         : {sink_rate:.6f} ps^-1")
    print(f"sink_site         : {sink_site}")
    print(f"source_site       : {args.source_site}")
    print(f"t_max             : {args.t_max_ps} ps")
    print()

    ratios = np.logspace(np.log10(args.ratio_min), np.log10(args.ratio_max), args.ratio_count)
    rows = sweep_transport(
        model, kappa, ratios, sink_site, sink_rate,
        args.source_site, args.t_max_ps, args.dt_ps,
    )
    print_results(rows)

    if args.csv_out is not None:
        write_csv(args.csv_out, rows)
        print(f"\nCSV written to: {args.csv_out}")


if __name__ == "__main__":
    main()
```

**Step 2: Run Phase 2**

Run: `.venv/bin/python3 -m enaqt_simulation.phase2_transport --csv-out results/phase2_transport.csv`

**Step 3: Commit**

```
git add enaqt_simulation/phase2_transport.py
git commit -m "implement Phase 2 ENAQT transport efficiency sweep"
```

---

### Task 5: Implement Phase 3 — Evolutionary Geometry Search

**Files:**
- Create: `enaqt_simulation/phase3_evolve.py`

**Step 1: Write `phase3_evolve.py`**

```python
"""Phase 3: Can evolution find microtubule geometries that maximize
quantum transport advantage?

Uses scipy.optimize.differential_evolution to search over helix geometry
parameters, maximizing transport efficiency at physiological dephasing.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    derive_kappa,
    reference_gap_ps_inv,
)
from enaqt_simulation.phase2_transport import compute_transport_efficiency


PARAM_BOUNDS = [
    (1.0, 4.0),    # helix_radius_nm
    (0.4, 1.5),    # helix_rise_nm
    (20.0, 40.0),  # helix_twist_deg
    (0.0, 45.0),   # dipole_tilt_deg
    (0.0, 100.0),  # disorder_cm
    (20.0, 120.0), # coupling_cm
]

PARAM_NAMES = [
    "helix_radius_nm", "helix_rise_nm", "helix_twist_deg",
    "dipole_tilt_deg", "disorder_cm", "coupling_cm",
]


def fitness(
    params: np.ndarray,
    sites: int,
    seed: int,
    bath_strength_cm: float,
    cutoff_cm: float,
    temperature_k: float,
    sink_rate_cm: float,
    t_max_ps: float,
    dt_ps: float,
) -> float:
    radius, rise, twist, tilt, disorder, coupling = params
    try:
        model = build_helix_model(
            sites=sites, coupling_cm=coupling, disorder_cm=disorder,
            seed=seed, helix_radius_nm=radius, helix_rise_nm=rise,
            helix_twist_deg=twist, dipole_tilt_deg=tilt,
        )
        omega_ref = reference_gap_ps_inv(model.hamiltonian)
        kappa = derive_kappa(omega_ref, bath_strength_cm, cutoff_cm, temperature_k)
        sink_rate = cm_to_rad_ps(sink_rate_cm)
        sink_site = sites - 1

        # Compute efficiency at physiological gamma/kappa ≈ 0.05
        gamma_physio = 0.05 * kappa
        eff_quantum, _ = compute_transport_efficiency(
            model, gamma_physio, kappa, sink_site, sink_rate, 0, t_max_ps, dt_ps,
        )

        # Compute classical baseline (gamma/kappa ≈ 0.0001)
        gamma_classical = 0.0001 * kappa
        eff_classical, _ = compute_transport_efficiency(
            model, gamma_classical, kappa, sink_site, sink_rate, 0, t_max_ps, dt_ps,
        )

        # Maximize quantum advantage (negative because DE minimizes)
        return -(eff_quantum - eff_classical)
    except Exception:
        return 0.0  # penalize invalid geometries


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3: Evolutionary geometry search.")
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--bath-strength-cm", type=float, default=35.0)
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument("--sink-rate-cm", type=float, default=1.0)
    parser.add_argument("--t-max-ps", type=float, default=20.0)
    parser.add_argument("--dt-ps", type=float, default=0.02)
    parser.add_argument("--maxiter", type=int, default=50)
    parser.add_argument("--popsize", type=int, default=15)
    parser.add_argument("--csv-out", type=Path, default=None)
    args = parser.parse_args()

    print("Phase 3: Evolutionary Geometry Search")
    print("=====================================")
    print()

    # First: evaluate the default (biological) geometry
    default_params = [2.0, 0.8, 27.7, 20.0, 25.0, 60.0]
    default_fitness = -fitness(
        np.array(default_params), args.sites, args.seed,
        args.bath_strength_cm, args.cutoff_cm, args.temperature_k,
        args.sink_rate_cm, args.t_max_ps, args.dt_ps,
    )
    print(f"Default geometry quantum advantage: {default_fitness:.8f}")
    print(f"Default params: {dict(zip(PARAM_NAMES, default_params))}")
    print()

    generation_log: list[dict] = []

    def callback(xk, convergence):
        gen = len(generation_log) + 1
        advantage = -fitness(
            xk, args.sites, args.seed,
            args.bath_strength_cm, args.cutoff_cm, args.temperature_k,
            args.sink_rate_cm, args.t_max_ps, args.dt_ps,
        )
        entry = {"generation": gen, "advantage": advantage}
        for name, val in zip(PARAM_NAMES, xk):
            entry[name] = val
        generation_log.append(entry)
        print(f"  gen {gen:3d}: advantage={advantage:.8f}  params={dict(zip(PARAM_NAMES, [f'{v:.3f}' for v in xk]))}")

    print("Running differential evolution...")
    result = differential_evolution(
        fitness,
        bounds=PARAM_BOUNDS,
        args=(
            args.sites, args.seed, args.bath_strength_cm,
            args.cutoff_cm, args.temperature_k, args.sink_rate_cm,
            args.t_max_ps, args.dt_ps,
        ),
        maxiter=args.maxiter,
        popsize=args.popsize,
        seed=args.seed,
        callback=callback,
        tol=1e-6,
    )

    optimized_advantage = -result.fun
    print()
    print(f"Optimized quantum advantage: {optimized_advantage:.8f}")
    print(f"Optimized params: {dict(zip(PARAM_NAMES, result.x))}")
    print(f"Improvement over default: {optimized_advantage - default_fitness:+.8f}")
    print()

    if optimized_advantage > default_fitness * 1.5:
        print("VERDICT: GA found substantially better geometries.")
        print("Evolution had room to optimize quantum transport.")
    elif optimized_advantage > default_fitness * 1.05:
        print("VERDICT: GA found modestly better geometries.")
        print("Default geometry is reasonable but not optimal.")
    else:
        print("VERDICT: Default geometry is near-optimal.")
        print("The 13-pf microtubule geometry may be pre-adapted for quantum transport.")

    if args.csv_out is not None:
        with args.csv_out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["generation", "advantage"] + PARAM_NAMES)
            writer.writeheader()
            for entry in generation_log:
                writer.writerow({k: f"{v:.8g}" if isinstance(v, float) else v for k, v in entry.items()})
        print(f"\nCSV written to: {args.csv_out}")


if __name__ == "__main__":
    main()
```

**Step 2: Run Phase 3**

Run: `.venv/bin/python3 -m enaqt_simulation.phase3_evolve --maxiter 30 --csv-out results/phase3_evolve.csv`

Note: This will take longer (minutes, not seconds). Use `--maxiter 10` for a quick test.

**Step 3: Commit**

```
git add enaqt_simulation/phase3_evolve.py
git commit -m "implement Phase 3 evolutionary geometry search"
```

---

### Task 6: Run full pipeline and document results

**Step 1: Create results directory**

Run: `mkdir -p results`

**Step 2: Run Phase 1**

Run: `.venv/bin/python3 -m enaqt_simulation.phase1_bias --csv-out results/phase1_bias.csv`

Capture output.

**Step 3: Run Phase 2 (only if Phase 1 shows bias)**

Run: `.venv/bin/python3 -m enaqt_simulation.phase2_transport --csv-out results/phase2_transport.csv`

Capture output.

**Step 4: Run Phase 3 (only if Phase 2 shows ENAQT)**

Run: `.venv/bin/python3 -m enaqt_simulation.phase3_evolve --maxiter 50 --csv-out results/phase3_evolve.csv`

Capture output.

**Step 5: Commit all results**

```
git add results/
git commit -m "ENAQT simulation results: Phase 1-3"
```
