"""
Phase 1 ENAQT bias test: does dephasing-assisted transport produce
measurable probability bias at physiological dephasing rates?

Sweeps gamma/kappa from 1e-4 (essentially classical) to 10 (strong coupling)
and measures three bias metrics relative to the classical reference:
  1. Trace distance of site populations
  2. Off-diagonal coherence magnitude
  3. Shannon entropy difference
"""

from __future__ import annotations

import argparse
import csv
from math import pi
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


def make_hamiltonian_at_gamma(
    model: HamiltonianModel, gamma: float
) -> np.ndarray:
    """
    Build H(gamma) = gamma * coupling_matrix + diag(cm_to_rad_ps(site_energies)).

    gamma scales the inter-site coupling strength while the on-site
    (disorder) potential remains fixed.
    """
    n = model.coupling_matrix.shape[0]
    h_pot = np.zeros((n, n), dtype=np.complex128)
    np.fill_diagonal(h_pot, cm_to_rad_ps(model.site_energies))
    return gamma * model.coupling_matrix + h_pot


def shannon_entropy(p: np.ndarray) -> float:
    """Shannon entropy of a probability vector (natural log)."""
    p_safe = p[p > 1e-30]
    return float(-np.sum(p_safe * np.log(p_safe)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 1 ENAQT bias sweep: gamma/kappa ratio scan."
    )
    # Helix geometry
    parser.add_argument("--sites", type=int, default=8)
    parser.add_argument("--coupling-cm", type=float, default=60.0)
    parser.add_argument("--disorder-cm", type=float, default=25.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--helix-radius-nm", type=float, default=2.0)
    parser.add_argument("--helix-rise-nm", type=float, default=0.8)
    parser.add_argument("--helix-twist-deg", type=float, default=27.7)
    parser.add_argument("--dipole-tilt-deg", type=float, default=20.0)
    # Bath
    parser.add_argument("--bath-strength-cm", type=float, default=35.0)
    parser.add_argument("--cutoff-cm", type=float, default=53.0)
    parser.add_argument("--temperature-k", type=float, default=310.0)
    # Sweep
    parser.add_argument("--ratio-min", type=float, default=1e-4)
    parser.add_argument("--ratio-max", type=float, default=10.0)
    parser.add_argument("--ratio-count", type=int, default=50)
    # Output
    parser.add_argument("--csv-out", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. Build helix model with default microtubule parameters
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

    # 2. Derive kappa from spectral density at physiological temperature
    omega_ref = reference_gap_ps_inv(model.hamiltonian)
    kappa = derive_kappa(
        omega_ref=omega_ref,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
        temperature_k=args.temperature_k,
    )

    print("ENAQT Phase 1: Probability Bias Test")
    print("=" * 60)
    print(f"model_label               : {model.label}")
    print(f"sites                     : {args.sites}")
    print(f"coupling_cm               : {args.coupling_cm}")
    print(f"disorder_cm               : {args.disorder_cm}")
    print(f"seed                      : {args.seed}")
    print(f"nn_coupling_median_cm     : {model.nearest_neighbor_median_cm:.6f}")
    print(f"all_pair_median_cm        : {model.all_pair_median_cm:.6f}")
    print(f"all_pair_max_cm           : {model.all_pair_max_cm:.6f}")
    print(f"bath_strength_cm          : {args.bath_strength_cm}")
    print(f"cutoff_cm                 : {args.cutoff_cm}")
    print(f"temperature_k             : {args.temperature_k}")
    print(f"reference_gap_ps_inv      : {omega_ref:.6f}")
    print(f"derived_kappa_ps_inv      : {kappa:.6f}")
    print(f"ratio_range               : [{args.ratio_min}, {args.ratio_max}]")
    print(f"ratio_count               : {args.ratio_count}")
    print()

    # 3. Sweep gamma/kappa ratio
    ratios = np.logspace(
        np.log10(args.ratio_min),
        np.log10(args.ratio_max),
        args.ratio_count,
    )
    gammas = ratios * kappa

    # 4. Compute steady states at each gamma/kappa
    populations_list: list[np.ndarray] = []
    coherences: list[float] = []
    rho_list: list[np.ndarray] = []

    for gamma in gammas:
        h = make_hamiltonian_at_gamma(model, gamma)
        liouv = build_liouvillian(h, kappa, model.coupling_matrix)
        rho_ss = steady_state(liouv, args.sites)
        pops = np.diag(rho_ss).real
        pops = np.clip(pops, 0.0, None)
        pops = pops / pops.sum()

        # Off-diagonal coherence
        off_diag = np.abs(rho_ss) - np.diag(np.diag(np.abs(rho_ss)))
        coherence = float(np.sum(off_diag))

        populations_list.append(pops)
        coherences.append(coherence)
        rho_list.append(rho_ss)

    # 5. Classical reference = gamma/kappa = ratio_min (first point)
    p_classical = populations_list[0]
    s_classical = shannon_entropy(p_classical)

    # 6. Compute bias metrics
    trace_distances: list[float] = []
    entropy_diffs: list[float] = []

    for pops in populations_list:
        td = 0.5 * float(np.sum(np.abs(pops - p_classical)))
        trace_distances.append(td)
        s_diff = shannon_entropy(pops) - s_classical
        entropy_diffs.append(s_diff)

    # 7. Print results table
    header = (
        f"{'ratio':>12} {'gamma_ps-1':>12} "
        f"{'trace_dist':>12} {'coherence':>12} {'dS_shannon':>12}"
    )
    print(header)
    print("-" * len(header))

    csv_rows: list[dict] = []
    for i, ratio in enumerate(ratios):
        row_str = (
            f"{ratio:12.6e} {gammas[i]:12.6e} "
            f"{trace_distances[i]:12.6e} {coherences[i]:12.6e} "
            f"{entropy_diffs[i]:12.6e}"
        )
        print(row_str)
        csv_rows.append(
            {
                "gamma_over_kappa": ratio,
                "gamma_ps_inv": gammas[i],
                "trace_distance": trace_distances[i],
                "coherence": coherences[i],
                "entropy_diff": entropy_diffs[i],
            }
        )

    # Summary statistics
    max_td = max(trace_distances)
    max_td_ratio = ratios[np.argmax(trace_distances)]
    max_coh = max(coherences)
    max_coh_ratio = ratios[np.argmax(coherences)]
    max_ds = max(np.abs(entropy_diffs))
    max_ds_ratio = ratios[int(np.argmax(np.abs(entropy_diffs)))]

    print()
    print("Summary")
    print("-" * 60)
    print(f"max trace distance        : {max_td:.6e}  (at ratio {max_td_ratio:.4e})")
    print(f"max coherence             : {max_coh:.6e}  (at ratio {max_coh_ratio:.4e})")
    print(f"max |dS| (Shannon)        : {max_ds:.6e}  (at ratio {max_ds_ratio:.4e})")
    print()

    # Verdict
    TRACE_DIST_THRESHOLD = 1e-3
    COHERENCE_THRESHOLD = 1e-4
    if max_td > TRACE_DIST_THRESHOLD:
        verdict = (
            "BIAS DETECTED: quantum coupling produces measurable redistribution "
            f"of steady-state populations (trace dist {max_td:.4e} > {TRACE_DIST_THRESHOLD})."
        )
    elif max_coh > COHERENCE_THRESHOLD:
        verdict = (
            "WEAK BIAS: populations nearly uniform but residual coherences "
            f"present (coherence {max_coh:.4e} > {COHERENCE_THRESHOLD})."
        )
    else:
        verdict = (
            "NO BIAS DETECTED: dephasing dominates at all coupling strengths; "
            "steady state is effectively classical (thermal)."
        )
    print(f"Verdict: {verdict}")

    # 8. Write CSV if requested
    if args.csv_out is not None:
        with args.csv_out.open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "gamma_over_kappa",
                    "gamma_ps_inv",
                    "trace_distance",
                    "coherence",
                    "entropy_diff",
                ],
            )
            writer.writeheader()
            for row in csv_rows:
                writer.writerow(
                    {k: f"{v:.12g}" for k, v in row.items()}
                )
        print()
        print(f"wrote_csv                 : {args.csv_out}")


if __name__ == "__main__":
    main()
