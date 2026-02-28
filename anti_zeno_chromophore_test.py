#!/usr/bin/env python3
"""
Stage-1 anti-Zeno test for a small tryptophan chromophore network.

What this script does:
1. Builds a small nearest-neighbor chromophore Hamiltonian with optional static
   disorder.
2. Defines a bath spectral density (Drude-Lorentz or Ohmic).
3. Derives a local dephasing rate kappa from the spectral density at a
   characteristic excitonic gap.
4. Evolves the open quantum system with a Lindblad generator.
5. Applies the standard repeated-measurement survival test and computes the
   effective decay / transition rate as a function of measurement interval.
6. Reports whether more frequent measurements push the system toward a Zeno or
   anti-Zeno regime over the scanned intervals.

This is intentionally a tractable, repeatable test rather than a full HEOM /
TEMPO treatment. It is useful for falsification and parameter exploration, but
it should be treated as a stage-1 model rather than a final biophysical claim.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from math import pi
from pathlib import Path

import numpy as np
from scipy.linalg import eigh, expm


CM_TO_RAD_PER_PS = 2.0 * pi * 29.9792458e9 / 1e12
KB_OVER_HBAR_PS_K = 1.380649e-23 / 1.054571817e-34 / 1e12
EPS = 1e-15


@dataclass
class SweepRow:
    tau_ps: float
    measurement_frequency_ps_inv: float
    survival_probability: float
    effective_rate_ps_inv: float
    local_regime: str


def cm_to_rad_ps(value_cm: float) -> float:
    return value_cm * CM_TO_RAD_PER_PS


def build_hamiltonian(
    sites: int,
    coupling_cm: float,
    disorder_cm: float,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h = np.zeros((sites, sites), dtype=np.complex128)

    if disorder_cm:
        disorder = rng.normal(0.0, disorder_cm, size=sites)
        np.fill_diagonal(h, cm_to_rad_ps(disorder))

    coupling = cm_to_rad_ps(coupling_cm)
    for i in range(sites - 1):
        h[i, i + 1] = coupling
        h[i + 1, i] = coupling
    return h


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
    spectral_density: str,
    bath_strength_cm: float,
    cutoff_cm: float,
    ohmic_exponent: float,
) -> float:
    if omega_ps_inv <= 0.0:
        return 0.0

    strength = cm_to_rad_ps(bath_strength_cm)
    cutoff = cm_to_rad_ps(cutoff_cm)

    if spectral_density == "drude":
        return 2.0 * strength * cutoff * omega_ps_inv / (
            omega_ps_inv**2 + cutoff**2
        )
    if spectral_density == "ohmic":
        return strength * (omega_ps_inv**ohmic_exponent) * np.exp(
            -omega_ps_inv / cutoff
        )
    raise ValueError(f"Unsupported spectral density: {spectral_density}")


def kappa_from_spectral_density(
    omega_ref_ps_inv: float,
    spectral_density: str,
    bath_strength_cm: float,
    cutoff_cm: float,
    ohmic_exponent: float,
    temperature_k: float,
    bath_scale: float,
) -> tuple[float, float]:
    j_value = spectral_density_ps_inv(
        omega_ps_inv=omega_ref_ps_inv,
        spectral_density=spectral_density,
        bath_strength_cm=bath_strength_cm,
        cutoff_cm=cutoff_cm,
        ohmic_exponent=ohmic_exponent,
    )
    kappa = bath_scale * 2.0 * pi * j_value * thermal_weight(
        omega_ref_ps_inv, temperature_k
    )
    return j_value, kappa


def liouvillian_local_dephasing(h: np.ndarray, kappa_ps_inv: float) -> np.ndarray:
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


def survival_probability(
    liouvillian: np.ndarray,
    sites: int,
    tau_ps: float,
    measurement_site: int,
) -> float:
    rho0 = np.zeros((sites, sites), dtype=np.complex128)
    rho0[measurement_site, measurement_site] = 1.0
    rho_t = expm(liouvillian * tau_ps) @ rho0.reshape(-1, order="F")
    rho_t = rho_t.reshape((sites, sites), order="F")
    return float(np.clip(rho_t[measurement_site, measurement_site].real, EPS, 1.0))


def effective_rate_ps_inv(survival: float, tau_ps: float) -> float:
    return float(-np.log(max(survival, EPS)) / tau_ps)


def classify_interval(rate_at_smaller_tau: float, rate_at_larger_tau: float) -> str:
    delta = rate_at_larger_tau - rate_at_smaller_tau
    if delta > 1e-9:
        return "zeno"
    if delta < -1e-9:
        return "anti-zeno"
    return "flat"


def summarize_regime(rows: list[SweepRow]) -> tuple[str, str, float | None]:
    interval_labels = [row.local_regime for row in rows[:-1] if row.local_regime != "n/a"]
    if not interval_labels:
        return "flat", "flat", None

    unique = set(interval_labels)
    high_freq = interval_labels[0]
    low_freq = interval_labels[-1]
    if len(unique) == 1:
        return high_freq, low_freq, None

    first = interval_labels[0]
    for index, label in enumerate(interval_labels[1:], start=1):
        if label != first:
            tau_left = rows[index - 1].tau_ps
            tau_right = rows[index].tau_ps
            crossover = float(np.sqrt(tau_left * tau_right))
            return high_freq, low_freq, crossover
    return high_freq, low_freq, None


def sweep_measurement_intervals(
    liouvillian: np.ndarray,
    sites: int,
    measurement_site: int,
    tau_min_ps: float,
    tau_max_ps: float,
    tau_count: int,
) -> list[SweepRow]:
    taus = np.logspace(np.log10(tau_min_ps), np.log10(tau_max_ps), tau_count)
    survivals = [
        survival_probability(liouvillian, sites, tau_ps, measurement_site)
        for tau_ps in taus
    ]
    rates = [effective_rate_ps_inv(survival, tau_ps) for survival, tau_ps in zip(survivals, taus)]

    rows: list[SweepRow] = []
    for index, tau_ps in enumerate(taus):
        if index < len(taus) - 1:
            local_regime = classify_interval(rates[index], rates[index + 1])
        else:
            local_regime = "n/a"
        rows.append(
            SweepRow(
                tau_ps=float(tau_ps),
                measurement_frequency_ps_inv=float(1.0 / tau_ps),
                survival_probability=float(survivals[index]),
                effective_rate_ps_inv=float(rates[index]),
                local_regime=local_regime,
            )
        )
    return rows


def write_csv(path: Path, rows: list[SweepRow]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "tau_ps",
                "measurement_frequency_ps_inv",
                "survival_probability",
                "effective_rate_ps_inv",
                "local_regime",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    f"{row.tau_ps:.12g}",
                    f"{row.measurement_frequency_ps_inv:.12g}",
                    f"{row.survival_probability:.12g}",
                    f"{row.effective_rate_ps_inv:.12g}",
                    row.local_regime,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repeatable Lindblad anti-Zeno test for a small chromophore network."
    )
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--coupling-cm", type=float, default=60.0)
    parser.add_argument("--disorder-cm", type=float, default=25.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--spectral-density",
        choices=("drude", "ohmic"),
        default="drude",
    )
    parser.add_argument(
        "--bath-strength-cm",
        type=float,
        default=35.0,
        help="Reorganization-like strength for Drude, coupling amplitude for Ohmic.",
    )
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--ohmic-exponent", type=float, default=1.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    parser.add_argument(
        "--bath-scale",
        type=float,
        default=1.0,
        help="Extra multiplicative factor on the derived dephasing rate.",
    )
    parser.add_argument(
        "--kappa-ps",
        type=float,
        default=None,
        help="Override the spectrally derived dephasing rate in ps^-1.",
    )
    parser.add_argument("--measurement-site", type=int, default=0)
    parser.add_argument("--tau-min-ps", type=float, default=1e-3)
    parser.add_argument("--tau-max-ps", type=float, default=5.0)
    parser.add_argument("--tau-count", type=int, default=18)
    parser.add_argument("--csv-out", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    h = build_hamiltonian(
        sites=args.sites,
        coupling_cm=args.coupling_cm,
        disorder_cm=args.disorder_cm,
        seed=args.seed,
    )
    omega_ref = reference_gap_ps_inv(h)

    j_value, derived_kappa = kappa_from_spectral_density(
        omega_ref_ps_inv=omega_ref,
        spectral_density=args.spectral_density,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
        ohmic_exponent=args.ohmic_exponent,
        temperature_k=args.temperature_k,
        bath_scale=args.bath_scale,
    )
    kappa = args.kappa_ps if args.kappa_ps is not None else derived_kappa

    liouvillian = liouvillian_local_dephasing(h, kappa)
    rows = sweep_measurement_intervals(
        liouvillian=liouvillian,
        sites=args.sites,
        measurement_site=args.measurement_site,
        tau_min_ps=args.tau_min_ps,
        tau_max_ps=args.tau_max_ps,
        tau_count=args.tau_count,
    )

    high_freq_regime, low_freq_regime, crossover_tau = summarize_regime(rows)

    print("Small open-quantum-system anti-Zeno test")
    print("----------------------------------------")
    print(f"sites                     : {args.sites}")
    print(f"coupling_cm               : {args.coupling_cm}")
    print(f"disorder_cm               : {args.disorder_cm}")
    print(f"seed                      : {args.seed}")
    print(f"spectral_density          : {args.spectral_density}")
    print(f"bath_strength_cm          : {args.bath_strength_cm}")
    print(f"cutoff_cm                 : {args.cutoff_cm}")
    print(f"temperature_k             : {args.temperature_k}")
    print(f"reference_gap_ps_inv      : {omega_ref:.6f}")
    print(f"J(omega_ref)_ps_inv       : {j_value:.6f}")
    print(f"derived_kappa_ps_inv      : {derived_kappa:.6f}")
    if args.kappa_ps is not None:
        print(f"override_kappa_ps_inv     : {args.kappa_ps:.6f}")
    print(f"measurement_site          : {args.measurement_site}")
    print(f"tau_range_ps              : [{args.tau_min_ps}, {args.tau_max_ps}]")
    print(f"tau_count                 : {args.tau_count}")
    print()
    print(f"high-frequency regime     : {high_freq_regime}")
    print(f"low-frequency regime      : {low_freq_regime}")
    if crossover_tau is None:
        print("first crossover tau_ps    : none detected")
    else:
        print(f"first crossover tau_ps    : {crossover_tau:.6f}")
    print()
    print(
        f"{'tau_ps':>12} {'freq_ps^-1':>12} {'survival':>12} {'rate_ps^-1':>12} {'interval':>12}"
    )
    for row in rows:
        print(
            f"{row.tau_ps:12.6f} "
            f"{row.measurement_frequency_ps_inv:12.6f} "
            f"{row.survival_probability:12.6f} "
            f"{row.effective_rate_ps_inv:12.6f} "
            f"{row.local_regime:>12}"
        )

    if args.csv_out is not None:
        write_csv(args.csv_out, rows)
        print()
        print(f"wrote_csv                 : {args.csv_out}")


if __name__ == "__main__":
    main()
