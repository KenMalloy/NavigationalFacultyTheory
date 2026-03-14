#!/usr/bin/env python3
r"""
Spectral-overlap analysis for the Zeno/anti-Zeno chapter.

This script does two related things with the same tryptophan-network defaults
used elsewhere in the repo:

1. It repeats the small open-system survival sweep used in
   ``anti_zeno_chromophore_test.py`` to extract a dynamical crossover between
   Zeno-like and anti-Zeno-like measurement intervals.
2. It computes a Kofman-Kurizki-style spectral-overlap proxy,
   R(tau) = 2 pi \int J(omega) F(omega, tau) d omega, to show why the
   crossover appears for a Drude-Lorentz environment with a structured peak.

The overlap model is intentionally simple: it is not the same master equation
as the open-system sweep. The point is not exact rate matching, but to show
that the bath spectral density and the measurement-induced frequency window
produce the same qualitative regime structure and a comparable crossover band.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("/tmp") / "codex-cache"))

import matplotlib
import numpy as np
from scipy.linalg import expm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from enaqt_simulation.core import (
    build_helix_model,
    cm_to_rad_ps,
    derive_kappa,
    reference_gap_ps_inv,
)


matplotlib.use("Agg")
import matplotlib.pyplot as plt


EPS = 1e-15


@dataclass
class SweepPoint:
    tau_ps: float
    measurement_frequency_ps_inv: float
    survival_probability: float
    survival_rate_ps_inv: float
    survival_regime: str
    overlap_rate_ps_inv: float
    overlap_regime: str


def drude_spectral_density_curve(
    omega_ps_inv: np.ndarray,
    bath_strength_cm: float,
    cutoff_cm: float,
) -> np.ndarray:
    """Vectorized Drude-Lorentz spectral density in ps^-1."""
    omega = np.asarray(omega_ps_inv, dtype=float)
    strength = float(cm_to_rad_ps(bath_strength_cm))
    cutoff = float(cm_to_rad_ps(cutoff_cm))
    density = np.zeros_like(omega)
    mask = omega > 0.0
    density[mask] = (
        2.0 * strength * cutoff * omega[mask] / (omega[mask] ** 2 + cutoff**2)
    )
    return density


def repeated_measurement_filter(
    omega_ps_inv: np.ndarray,
    tau_ps: float,
) -> np.ndarray:
    """
    Measurement filter in frequency space.

    We use the standard sinc^2 window induced by repeated measurements. In this
    simple proxy model, smaller ``tau_ps`` broadens the filter and samples a
    wider portion of the bath spectrum.
    """
    omega = np.asarray(omega_ps_inv, dtype=float)
    argument = 0.5 * omega * tau_ps
    return (tau_ps / (2.0 * np.pi)) * np.sinc(argument / np.pi) ** 2


def overlap_rate_ps_inv(
    omega_grid_ps_inv: np.ndarray,
    spectral_density: np.ndarray,
    tau_ps: float,
) -> float:
    filter_values = repeated_measurement_filter(omega_grid_ps_inv, tau_ps)
    return float(
        2.0
        * np.pi
        * np.trapezoid(spectral_density * filter_values, omega_grid_ps_inv)
    )


def liouvillian_local_dephasing(h: np.ndarray, kappa_ps_inv: float) -> np.ndarray:
    """Same local-dephasing model used in anti_zeno_chromophore_test.py."""
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


def classify_intervals(rates: np.ndarray) -> list[str]:
    labels: list[str] = []
    for rate_now, rate_next in zip(rates[:-1], rates[1:]):
        delta = float(rate_next - rate_now)
        if delta > 1e-9:
            labels.append("zeno")
        elif delta < -1e-9:
            labels.append("anti-zeno")
        else:
            labels.append("flat")
    labels.append("n/a")
    return labels


def first_crossover_tau(
    taus_ps: np.ndarray,
    interval_labels: list[str],
) -> float | None:
    valid = interval_labels[:-1]
    if not valid:
        return None

    first = valid[0]
    for index, label in enumerate(valid[1:], start=1):
        if label != first:
            return float(np.sqrt(taus_ps[index - 1] * taus_ps[index]))
    return None


def representative_taus(
    tau_min_ps: float,
    tau_max_ps: float,
    overlap_crossover_tau_ps: float | None,
    dynamic_crossover_tau_ps: float | None,
) -> list[tuple[str, float]]:
    samples: list[tuple[str, float]] = [
        ("high-freq Zeno", min(0.01, tau_max_ps)),
    ]

    if overlap_crossover_tau_ps is not None:
        samples.append(("overlap max", overlap_crossover_tau_ps))
    if dynamic_crossover_tau_ps is not None:
        samples.append(("dynamic crossover", dynamic_crossover_tau_ps))

    samples.append(("low-freq anti-Zeno", max(1.0, tau_min_ps)))

    deduped: list[tuple[str, float]] = []
    seen: set[int] = set()
    for label, tau_ps in samples:
        rounded = int(round(tau_ps * 1_000_000))
        if rounded in seen:
            continue
        seen.add(rounded)
        deduped.append((label, tau_ps))
    return deduped


def write_csv(path: Path, rows: list[SweepPoint]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "tau_ps",
                "measurement_frequency_ps_inv",
                "survival_probability",
                "survival_rate_ps_inv",
                "survival_regime",
                "overlap_rate_ps_inv",
                "overlap_regime",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    f"{row.tau_ps:.12g}",
                    f"{row.measurement_frequency_ps_inv:.12g}",
                    f"{row.survival_probability:.12g}",
                    f"{row.survival_rate_ps_inv:.12g}",
                    row.survival_regime,
                    f"{row.overlap_rate_ps_inv:.12g}",
                    row.overlap_regime,
                ]
            )


def make_plot(
    figure_out: Path,
    omega_plot_ps_inv: np.ndarray,
    spectral_density_plot: np.ndarray,
    filter_samples: list[tuple[str, float]],
    rows: list[SweepPoint],
    cutoff_ps_inv: float,
    overlap_crossover_tau_ps: float | None,
    dynamic_crossover_tau_ps: float | None,
) -> None:
    freqs = np.array([row.measurement_frequency_ps_inv for row in rows], dtype=float)
    survival_rates = np.array([row.survival_rate_ps_inv for row in rows], dtype=float)
    overlap_rates = np.array([row.overlap_rate_ps_inv for row in rows], dtype=float)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))

    ax0 = axes[0]
    ax0.plot(
        omega_plot_ps_inv,
        spectral_density_plot,
        color="#0f766e",
        linewidth=2.2,
        label="Drude-Lorentz spectral density",
    )
    for label, tau_ps in filter_samples:
        filter_values = repeated_measurement_filter(omega_plot_ps_inv, tau_ps)
        scaled_filter = (
            filter_values / max(float(filter_values.max()), EPS) * spectral_density_plot.max()
        )
        ax0.plot(
            omega_plot_ps_inv,
            scaled_filter,
            linewidth=1.6,
            linestyle="--",
            label=f"{label}: tau={tau_ps:.3f} ps",
        )
    ax0.axvline(
        cutoff_ps_inv,
        color="#7c3aed",
        linewidth=1.2,
        linestyle=":",
        label=f"bath peak ~ {cutoff_ps_inv:.2f} ps^-1",
    )
    ax0.set_xlabel("Frequency (ps^-1)")
    ax0.set_ylabel("J(omega) and scaled filters")
    ax0.set_title("Bath Spectrum vs Measurement Window")
    ax0.set_xlim(0.0, float(omega_plot_ps_inv.max()))
    ax0.legend(fontsize=8, frameon=False)

    ax1 = axes[1]
    ax1.plot(freqs, survival_rates, color="#1d4ed8", linewidth=2.2)
    if dynamic_crossover_tau_ps is not None:
        ax1.axvline(
            1.0 / dynamic_crossover_tau_ps,
            color="#dc2626",
            linestyle="--",
            linewidth=1.4,
            label=f"crossover ~ {1.0 / dynamic_crossover_tau_ps:.2f} ps^-1",
        )
        ax1.legend(fontsize=8, frameon=False)
    ax1.set_xscale("log")
    ax1.set_xlabel("Measurement frequency (ps^-1)")
    ax1.set_ylabel("Effective decay rate (ps^-1)")
    ax1.set_title("Open-System Survival Sweep")

    ax2 = axes[2]
    ax2.plot(freqs, overlap_rates, color="#ea580c", linewidth=2.2)
    if overlap_crossover_tau_ps is not None:
        ax2.axvline(
            1.0 / overlap_crossover_tau_ps,
            color="#dc2626",
            linestyle="--",
            linewidth=1.4,
            label=f"crossover ~ {1.0 / overlap_crossover_tau_ps:.2f} ps^-1",
        )
        ax2.legend(fontsize=8, frameon=False)
    ax2.set_xscale("log")
    ax2.set_xlabel("Measurement frequency (ps^-1)")
    ax2.set_ylabel("Overlap proxy R(tau) (ps^-1)")
    ax2.set_title("Kofman-Kurizki Overlap Proxy")

    fig.suptitle("Zeno/Anti-Zeno Crossover in the Tryptophan Helix Model", fontsize=13)
    fig.tight_layout()
    figure_out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_out, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spectral-overlap analysis for the Zeno/anti-Zeno chapter."
    )
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
    parser.add_argument("--measurement-site", type=int, default=0)
    parser.add_argument("--tau-min-ps", type=float, default=1e-3)
    parser.add_argument("--tau-max-ps", type=float, default=5.0)
    parser.add_argument("--tau-count", type=int, default=200)
    parser.add_argument("--omega-max-ps", type=float, default=4000.0)
    parser.add_argument("--omega-points", type=int, default=160000)
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=Path("simulations/anti_zeno_spectral_overlap.csv"),
    )
    parser.add_argument(
        "--figure-out",
        type=Path,
        default=Path("figures/anti_zeno_spectral_overlap.png"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

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

    omega_ref_ps_inv = reference_gap_ps_inv(model.hamiltonian)
    cutoff_ps_inv = float(cm_to_rad_ps(args.cutoff_cm))
    kappa_ps_inv = derive_kappa(
        omega_ref=omega_ref_ps_inv,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
        temperature_k=args.temperature_k,
    )

    taus_ps = np.logspace(
        np.log10(args.tau_min_ps),
        np.log10(args.tau_max_ps),
        args.tau_count,
    )
    measurement_freqs = 1.0 / taus_ps

    liouvillian = liouvillian_local_dephasing(model.hamiltonian, kappa_ps_inv)
    survivals = np.array(
        [
            survival_probability(
                liouvillian=liouvillian,
                sites=args.sites,
                tau_ps=float(tau_ps),
                measurement_site=args.measurement_site,
            )
            for tau_ps in taus_ps
        ],
        dtype=float,
    )
    survival_rates = np.array(
        [
            effective_rate_ps_inv(survival=float(survival), tau_ps=float(tau_ps))
            for survival, tau_ps in zip(survivals, taus_ps)
        ],
        dtype=float,
    )

    omega_grid_ps_inv = np.linspace(1e-6, args.omega_max_ps, args.omega_points)
    spectral_density = drude_spectral_density_curve(
        omega_grid_ps_inv,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
    )
    overlap_rates = np.array(
        [
            overlap_rate_ps_inv(
                omega_grid_ps_inv=omega_grid_ps_inv,
                spectral_density=spectral_density,
                tau_ps=float(tau_ps),
            )
            for tau_ps in taus_ps
        ],
        dtype=float,
    )

    survival_regimes = classify_intervals(survival_rates)
    overlap_regimes = classify_intervals(overlap_rates)
    dynamic_crossover_tau_ps = first_crossover_tau(taus_ps, survival_regimes)
    overlap_crossover_tau_ps = first_crossover_tau(taus_ps, overlap_regimes)

    rows = [
        SweepPoint(
            tau_ps=float(tau_ps),
            measurement_frequency_ps_inv=float(freq_ps_inv),
            survival_probability=float(survival),
            survival_rate_ps_inv=float(survival_rate),
            survival_regime=survival_regime,
            overlap_rate_ps_inv=float(overlap_rate),
            overlap_regime=overlap_regime,
        )
        for tau_ps, freq_ps_inv, survival, survival_rate, survival_regime, overlap_rate, overlap_regime in zip(
            taus_ps,
            measurement_freqs,
            survivals,
            survival_rates,
            survival_regimes,
            overlap_rates,
            overlap_regimes,
        )
    ]

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.csv_out, rows)

    omega_plot_max = min(40.0, cutoff_ps_inv * 4.0)
    omega_plot_ps_inv = np.linspace(1e-6, omega_plot_max, 4000)
    spectral_density_plot = drude_spectral_density_curve(
        omega_plot_ps_inv,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
    )
    filter_samples = representative_taus(
        tau_min_ps=args.tau_min_ps,
        tau_max_ps=args.tau_max_ps,
        overlap_crossover_tau_ps=overlap_crossover_tau_ps,
        dynamic_crossover_tau_ps=dynamic_crossover_tau_ps,
    )
    make_plot(
        figure_out=args.figure_out,
        omega_plot_ps_inv=omega_plot_ps_inv,
        spectral_density_plot=spectral_density_plot,
        filter_samples=filter_samples,
        rows=rows,
        cutoff_ps_inv=cutoff_ps_inv,
        overlap_crossover_tau_ps=overlap_crossover_tau_ps,
        dynamic_crossover_tau_ps=dynamic_crossover_tau_ps,
    )

    dynamic_peak_index = int(np.argmax(survival_rates))
    overlap_peak_index = int(np.argmax(overlap_rates))

    print("Anti-Zeno spectral-overlap analysis")
    print("-----------------------------------")
    print(f"model_label                 : {model.label}")
    print(f"sites                       : {args.sites}")
    print(f"reference_gap_ps_inv        : {omega_ref_ps_inv:.6f}")
    print(f"bath_peak_ps_inv            : {cutoff_ps_inv:.6f}")
    print(f"derived_kappa_ps_inv        : {kappa_ps_inv:.6f}")
    print(f"tau_range_ps                : [{args.tau_min_ps}, {args.tau_max_ps}]")
    print(f"tau_count                   : {args.tau_count}")
    print()
    print(
        "dynamic_peak_freq_ps_inv    : "
        f"{measurement_freqs[dynamic_peak_index]:.6f}"
    )
    print(
        "dynamic_peak_tau_ps         : "
        f"{taus_ps[dynamic_peak_index]:.6f}"
    )
    if dynamic_crossover_tau_ps is None:
        print("dynamic_crossover_tau_ps    : none detected")
    else:
        print(f"dynamic_crossover_tau_ps    : {dynamic_crossover_tau_ps:.6f}")
        print(
            "dynamic_crossover_freq_ps_inv: "
            f"{1.0 / dynamic_crossover_tau_ps:.6f}"
        )
        print(
            "dynamic_crossover_freq_us_inv: "
            f"{1.0e6 / dynamic_crossover_tau_ps:.6f}"
        )
    print()
    print(
        "overlap_peak_freq_ps_inv    : "
        f"{measurement_freqs[overlap_peak_index]:.6f}"
    )
    print(
        "overlap_peak_tau_ps         : "
        f"{taus_ps[overlap_peak_index]:.6f}"
    )
    if overlap_crossover_tau_ps is None:
        print("overlap_crossover_tau_ps    : none detected")
    else:
        print(f"overlap_crossover_tau_ps    : {overlap_crossover_tau_ps:.6f}")
        print(
            "overlap_crossover_freq_ps_inv: "
            f"{1.0 / overlap_crossover_tau_ps:.6f}"
        )
        print(
            "overlap_crossover_freq_us_inv: "
            f"{1.0e6 / overlap_crossover_tau_ps:.6f}"
        )
    print()
    print(f"csv_out                     : {args.csv_out}")
    print(f"figure_out                  : {args.figure_out}")


if __name__ == "__main__":
    main()
