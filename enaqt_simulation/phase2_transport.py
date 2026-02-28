"""
Phase 2 ENAQT transport efficiency test: does environment-assisted quantum
transport produce a directional transport advantage?

Fixes the Hamiltonian at the physical coupling strength and sweeps the
dephasing rate kappa across a wide range.  At each kappa value, the
Liouvillian (with irreversible sink on the last site) is built and
time-evolved from rho(0) = |source><source|.

Transport efficiency = 1 - Tr(rho(T_max)), i.e. the total population
captured by the sink.

ENAQT signature: efficiency peaks at an intermediate dephasing rate,
demonstrating that noise-assisted transport outperforms both the purely
coherent (kappa -> 0) and the noise-dominated (kappa -> inf) regimes.
"""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 2 ENAQT transport efficiency sweep."
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
    # Sweep: gamma/kappa ratio (gamma = coupling scale, kappa = dephasing)
    # We fix gamma = 1 (physical Hamiltonian) and sweep kappa = V / ratio
    # Range must be wide enough to span from dephasing-dominated to coherent
    parser.add_argument("--ratio-min", type=float, default=1e-3)
    parser.add_argument("--ratio-max", type=float, default=1e3)
    parser.add_argument("--ratio-count", type=int, default=40)
    # Sink / source
    parser.add_argument("--sink-site", type=int, default=-1,
                        help="Sink site index (-1 = last site)")
    parser.add_argument("--sink-rate-cm", type=float, default=1.0,
                        help="Sink trapping rate in cm^-1")
    parser.add_argument("--source-site", type=int, default=0,
                        help="Initial excitation site")
    # Time evolution
    parser.add_argument("--t-max-ps", type=float, default=50.0,
                        help="Maximum simulation time in ps")
    parser.add_argument("--dt-ps", type=float, default=0.05,
                        help="Time step in ps")
    # Output
    parser.add_argument("--csv-out", type=Path, default=None)
    return parser.parse_args()


def compute_transport_efficiency(
    liouvillian: np.ndarray,
    sites: int,
    source_site: int,
    t_max: float,
    dt: float,
) -> tuple[float, float]:
    """
    Time-evolve rho(0) = |source><source| under the Liouvillian and compute:
      - transport efficiency = 1 - Tr(rho(T_max))
        (total population captured by sink)
      - mean transfer time = weighted average of capture times

    Returns (efficiency, mean_transfer_time).
    """
    n2 = liouvillian.shape[0]
    n = sites

    # Initial state: |source><source|
    rho0 = np.zeros((n, n), dtype=np.complex128)
    rho0[source_site, source_site] = 1.0
    # Vectorize (column-major / Fortran order)
    rho_vec = rho0.reshape(n2, order="F")

    # Propagator for one time step
    propagator = expm(liouvillian * dt)

    n_steps = int(round(t_max / dt))

    # Track population trace over time for mean transfer time
    trace_prev = 1.0
    weighted_time_sum = 0.0
    total_captured = 0.0

    for step in range(1, n_steps + 1):
        rho_vec = propagator @ rho_vec
        rho = rho_vec.reshape((n, n), order="F")
        trace_now = np.real(np.trace(rho))

        # Population lost in this step
        delta_pop = trace_prev - trace_now
        if delta_pop > 0:
            t_mid = (step - 0.5) * dt
            weighted_time_sum += t_mid * delta_pop
            total_captured += delta_pop

        trace_prev = trace_now

    efficiency = 1.0 - trace_prev  # total population lost to sink

    if total_captured > 1e-15:
        mean_transfer_time = weighted_time_sum / total_captured
    else:
        mean_transfer_time = t_max  # nothing transferred

    return float(efficiency), float(mean_transfer_time)


def main() -> None:
    args = parse_args()

    # Resolve sink site
    sink_site = args.sink_site
    if sink_site < 0:
        sink_site = args.sites + sink_site  # -1 -> last site

    sink_rate = cm_to_rad_ps(args.sink_rate_cm)

    # 1. Build helix model
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

    # 2. Derive the physiological kappa from spectral density
    omega_ref = reference_gap_ps_inv(model.hamiltonian)
    kappa_phys = derive_kappa(
        omega_ref=omega_ref,
        bath_strength_cm=args.bath_strength_cm,
        cutoff_cm=args.cutoff_cm,
        temperature_k=args.temperature_k,
    )

    # The physical Hamiltonian is model.hamiltonian (gamma = 1).
    # A characteristic coherent coupling scale V is the nearest-neighbour
    # coupling in rad/ps.
    V = cm_to_rad_ps(model.nearest_neighbor_median_cm)  # rad/ps

    print("ENAQT Phase 2: Transport Efficiency Test")
    print("=" * 65)
    print(f"model_label               : {model.label}")
    print(f"sites                     : {args.sites}")
    print(f"coupling_cm               : {args.coupling_cm}")
    print(f"disorder_cm               : {args.disorder_cm}")
    print(f"seed                      : {args.seed}")
    print(f"nn_coupling_median_cm     : {model.nearest_neighbor_median_cm:.6f}")
    print(f"all_pair_median_cm        : {model.all_pair_median_cm:.6f}")
    print(f"all_pair_max_cm           : {model.all_pair_max_cm:.6f}")
    print(f"V (nn coupling, rad/ps)   : {V:.6f}")
    print(f"bath_strength_cm          : {args.bath_strength_cm}")
    print(f"cutoff_cm                 : {args.cutoff_cm}")
    print(f"temperature_k             : {args.temperature_k}")
    print(f"reference_gap_ps_inv      : {omega_ref:.6f}")
    print(f"kappa_phys_ps_inv         : {kappa_phys:.6f}")
    print(f"kappa_phys / V            : {kappa_phys / V:.6f}")
    print(f"source_site               : {args.source_site}")
    print(f"sink_site                 : {sink_site}")
    print(f"sink_rate_cm              : {args.sink_rate_cm}")
    print(f"sink_rate_ps_inv          : {sink_rate:.6f}")
    print(f"t_max_ps                  : {args.t_max_ps}")
    print(f"dt_ps                     : {args.dt_ps}")
    print(f"gamma/kappa ratio range   : [{args.ratio_min}, {args.ratio_max}]")
    print(f"ratio_count               : {args.ratio_count}")
    print()

    # 3. Sweep gamma/kappa ratio
    #
    # gamma/kappa = V / kappa  =>  kappa = V / ratio
    #
    # Low  gamma/kappa -> high kappa -> strong dephasing (classical limit)
    # High gamma/kappa -> low  kappa -> weak  dephasing (coherent limit)
    #
    # ENAQT: efficiency peaks at intermediate ratio.
    ratios = np.logspace(
        np.log10(args.ratio_min),
        np.log10(args.ratio_max),
        args.ratio_count,
    )
    kappas = V / ratios  # dephasing rate at each ratio

    # Fixed Hamiltonian (physical coupling strength, gamma = 1)
    h_fixed = model.hamiltonian

    efficiencies: list[float] = []
    mean_times: list[float] = []

    for idx, (ratio, kappa_val) in enumerate(zip(ratios, kappas)):
        liouv = build_liouvillian_with_sink(
            h=h_fixed,
            kappa_ps_inv=kappa_val,
            coupling_matrix=model.coupling_matrix,
            sink_site=sink_site,
            sink_rate_ps_inv=sink_rate,
        )
        eff, mtt = compute_transport_efficiency(
            liouvillian=liouv,
            sites=args.sites,
            source_site=args.source_site,
            t_max=args.t_max_ps,
            dt=args.dt_ps,
        )
        efficiencies.append(eff)
        mean_times.append(mtt)
        print(
            f"  [{idx+1:3d}/{args.ratio_count}] "
            f"gamma/kappa={ratio:12.6e}  "
            f"kappa={kappa_val:12.4e} ps-1  "
            f"efficiency={eff:8.5f}  "
            f"mean_time={mtt:8.3f} ps"
        )

    # 4. Print results table
    print()
    header = (
        f"{'gamma/kappa':>12} {'kappa_ps-1':>12} "
        f"{'efficiency':>12} {'mean_time_ps':>14}"
    )
    print(header)
    print("-" * len(header))

    for i, ratio in enumerate(ratios):
        print(
            f"{ratio:12.6e} {kappas[i]:12.6e} "
            f"{efficiencies[i]:12.6e} {mean_times[i]:14.6e}"
        )

    # 5. Summary and verdict
    print()
    print("Summary")
    print("-" * 65)

    max_eff = max(efficiencies)
    max_eff_idx = int(np.argmax(efficiencies))
    max_eff_ratio = ratios[max_eff_idx]
    max_eff_kappa = kappas[max_eff_idx]
    min_eff = min(efficiencies)
    min_eff_ratio = ratios[int(np.argmin(efficiencies))]
    min_mtt = min(mean_times)
    min_mtt_ratio = ratios[int(np.argmin(mean_times))]

    print(f"max efficiency            : {max_eff:.6f}  (at gamma/kappa = {max_eff_ratio:.4e}, kappa = {max_eff_kappa:.4e} ps-1)")
    print(f"min efficiency            : {min_eff:.6f}  (at gamma/kappa = {min_eff_ratio:.4e})")
    print(f"min mean transfer time    : {min_mtt:.3f} ps  (at gamma/kappa = {min_mtt_ratio:.4e})")
    print(f"physiological kappa/V     : {kappa_phys / V:.4e}  (gamma/kappa = {V / kappa_phys:.4e})")
    print()

    # Check for ENAQT: look for a local maximum in the efficiency curve
    # at intermediate gamma/kappa values.  The global max may be at an
    # endpoint if the coherent regime has high ballistic transport, but
    # the ENAQT signature is a *local* peak where noise-assisted transport
    # outperforms both neighbouring regimes.
    eff_arr = np.array(efficiencies)
    eff_low_ratio = efficiencies[0]   # low gamma/kappa = strong dephasing
    eff_high_ratio = efficiencies[-1]  # high gamma/kappa = weak dephasing

    # Find local maxima (interior points higher than both neighbours)
    local_max_indices = []
    for k in range(1, len(eff_arr) - 1):
        if eff_arr[k] > eff_arr[k - 1] and eff_arr[k] > eff_arr[k + 1]:
            local_max_indices.append(k)

    # Also check if the global max is at an interior point
    is_at_low_end = max_eff_idx <= 2
    is_at_high_end = max_eff_idx >= args.ratio_count - 3

    # Primary check: global max at interior
    peak_advantage_over_classical = max_eff - eff_low_ratio
    peak_advantage_over_coherent = max_eff - eff_high_ratio

    ADVANTAGE_THRESHOLD = 0.005  # 0.5% advantage required

    if (
        not is_at_low_end
        and not is_at_high_end
        and peak_advantage_over_classical > ADVANTAGE_THRESHOLD
        and peak_advantage_over_coherent > ADVANTAGE_THRESHOLD
    ):
        verdict = (
            "ENAQT DETECTED: transport efficiency peaks at intermediate "
            f"gamma/kappa = {max_eff_ratio:.4e} (efficiency = {max_eff:.4f}), "
            f"exceeding both the strong-dephasing limit ({eff_low_ratio:.4f}, gamma/kappa={ratios[0]:.1e}) and "
            f"the coherent limit ({eff_high_ratio:.4f}, gamma/kappa={ratios[-1]:.1e}). "
            f"Peak advantage: +{peak_advantage_over_classical:.4f} over classical, "
            f"+{peak_advantage_over_coherent:.4f} over coherent."
        )
    elif local_max_indices:
        # Secondary check: local maximum at interior (even if global max is at endpoint)
        best_local = max(local_max_indices, key=lambda k: eff_arr[k])
        local_peak_eff = eff_arr[best_local]
        local_peak_ratio = ratios[best_local]
        local_peak_kappa = kappas[best_local]
        # Find the local minimum between classical and this peak
        left_min = float(np.min(eff_arr[:best_local + 1]))
        # Find the local minimum between this peak and coherent end
        right_min = float(np.min(eff_arr[best_local:]))
        local_advantage = min(local_peak_eff - left_min, local_peak_eff - right_min)
        if local_advantage > ADVANTAGE_THRESHOLD:
            verdict = (
                "ENAQT DETECTED: transport efficiency shows a local maximum at "
                f"gamma/kappa = {local_peak_ratio:.4e} (kappa = {local_peak_kappa:.4e} ps-1, "
                f"efficiency = {local_peak_eff:.4f}), with dip advantage of "
                f"{local_advantage:.4f}. Noise-assisted transport outperforms "
                f"both the purely coherent and purely classical regimes locally. "
                f"Classical limit eff = {eff_low_ratio:.4f}, coherent limit eff = {eff_high_ratio:.4f}."
            )
        else:
            verdict = (
                f"MARGINAL ENAQT: local peak at gamma/kappa = {local_peak_ratio:.4e} "
                f"(eff = {local_peak_eff:.4f}), but local advantage ({local_advantage:.4f}) "
                f"is below threshold {ADVANTAGE_THRESHOLD}."
            )
    elif is_at_low_end:
        verdict = (
            "NO ENAQT: transport efficiency is highest in the strong-dephasing "
            f"(classical) regime (gamma/kappa = {max_eff_ratio:.4e}, "
            f"efficiency = {max_eff:.4f}). Classical hopping dominates."
        )
    elif is_at_high_end:
        verdict = (
            "NO ENAQT: transport efficiency is highest in the coherent regime "
            f"(gamma/kappa = {max_eff_ratio:.4e}, efficiency = {max_eff:.4f}). "
            "Dephasing does not enhance transport."
        )
    else:
        verdict = (
            f"MARGINAL: efficiency peak at gamma/kappa = {max_eff_ratio:.4e} "
            f"(eff = {max_eff:.4f}), but the advantage over endpoints is "
            f"too small (< {ADVANTAGE_THRESHOLD}) to claim ENAQT."
        )

    print(f"Verdict: {verdict}")

    # 6. Write CSV if requested
    if args.csv_out is not None:
        import csv
        with args.csv_out.open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "gamma_over_kappa",
                    "kappa_ps_inv",
                    "efficiency",
                    "mean_transfer_time_ps",
                ],
            )
            writer.writeheader()
            for i in range(len(ratios)):
                writer.writerow({
                    "gamma_over_kappa": f"{ratios[i]:.12g}",
                    "kappa_ps_inv": f"{kappas[i]:.12g}",
                    "efficiency": f"{efficiencies[i]:.12g}",
                    "mean_transfer_time_ps": f"{mean_times[i]:.12g}",
                })
        print()
        print(f"wrote_csv                 : {args.csv_out}")


if __name__ == "__main__":
    main()
