"""
Core building blocks for ENAQT (Environment-Assisted Quantum Transport)
simulations on microtubule chromophore networks.

Extracted and adapted from anti_zeno_chromophore_test.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np
from scipy.linalg import eigh, svd


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

CM_TO_RAD_PER_PS = 2.0 * pi * 29.9792458e9 / 1e12
KB_OVER_HBAR_PS_K = 1.380649e-23 / 1.054571817e-34 / 1e12
EPS = 1e-15


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class HamiltonianModel:
    hamiltonian: np.ndarray
    label: str
    nearest_neighbor_median_cm: float
    all_pair_median_cm: float
    all_pair_max_cm: float
    coupling_matrix: np.ndarray       # pure dipole-coupling matrix in rad/ps
    site_energies: np.ndarray         # diagonal disorder values in cm^-1


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def cm_to_rad_ps(value_cm: float | np.ndarray) -> float | np.ndarray:
    return value_cm * CM_TO_RAD_PER_PS


def rad_ps_to_cm(value_rad_ps: float | np.ndarray) -> float | np.ndarray:
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
    all_pairs = [
        couplings_cm[i, j] for i in range(sites) for j in range(i + 1, sites)
    ]
    return (
        float(np.median(nearest_neighbor)),
        float(np.median(all_pairs)),
        float(np.max(all_pairs)),
    )


# ---------------------------------------------------------------------------
# Hamiltonian builder
# ---------------------------------------------------------------------------

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
    h = np.zeros((sites, sites), dtype=np.complex128)

    # Static disorder on diagonal (stored in cm^-1)
    if disorder_cm:
        disorder = rng.normal(0.0, disorder_cm, size=sites)
    else:
        disorder = np.zeros(sites, dtype=float)
    site_energies = disorder.copy()

    np.fill_diagonal(h, cm_to_rad_ps(disorder))

    # Helix geometry
    positions: list[np.ndarray] = []
    dipoles: list[np.ndarray] = []
    twist_rad = np.deg2rad(helix_twist_deg)
    tilt_rad = np.deg2rad(dipole_tilt_deg)

    for index in range(sites):
        angle = index * twist_rad
        positions.append(
            np.array(
                [
                    helix_radius_nm * np.cos(angle),
                    helix_radius_nm * np.sin(angle),
                    index * helix_rise_nm,
                ],
                dtype=float,
            )
        )
        tangent = np.array([-np.sin(angle), np.cos(angle), 0.0], dtype=float)
        axial = np.array([0.0, 0.0, 1.0], dtype=float)
        dipole = np.cos(tilt_rad) * tangent + np.sin(tilt_rad) * axial
        dipoles.append(unit_vector(dipole))

    raw_couplings = np.zeros((sites, sites), dtype=float)
    for i in range(sites):
        for j in range(i + 1, sites):
            displacement = positions[j] - positions[i]
            distance = np.linalg.norm(displacement)
            direction = displacement / distance
            orientation = np.dot(dipoles[i], dipoles[j]) - 3.0 * np.dot(
                dipoles[i], direction
            ) * np.dot(dipoles[j], direction)
            raw_value = orientation / (distance**3)
            raw_couplings[i, j] = raw_value
            raw_couplings[j, i] = raw_value

    nearest_neighbor_raw = np.abs(
        np.array(
            [raw_couplings[i, i + 1] for i in range(sites - 1)], dtype=float
        )
    )
    raw_scale = coupling_cm / max(float(np.median(nearest_neighbor_raw)), EPS)
    coupling_matrix_cm = raw_scale * raw_couplings
    coupling_matrix_rad_ps = cm_to_rad_ps(coupling_matrix_cm)

    h += coupling_matrix_rad_ps

    nn_median_cm, all_pair_median_cm, all_pair_max_cm = summarize_couplings(h)
    return HamiltonianModel(
        hamiltonian=h,
        label=(
            "geometry-informed helix "
            f"(radius={helix_radius_nm} nm, rise={helix_rise_nm} nm, "
            f"twist={helix_twist_deg} deg, tilt={dipole_tilt_deg} deg)"
        ),
        nearest_neighbor_median_cm=nn_median_cm,
        all_pair_median_cm=all_pair_median_cm,
        all_pair_max_cm=all_pair_max_cm,
        coupling_matrix=coupling_matrix_rad_ps.copy(),
        site_energies=site_energies,
    )


# ---------------------------------------------------------------------------
# Bath / spectral-density helpers
# ---------------------------------------------------------------------------

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
    """Drude-Lorentz spectral density J(omega) in ps^-1."""
    if omega_ps_inv <= 0.0:
        return 0.0
    strength = cm_to_rad_ps(bath_strength_cm)
    cutoff = cm_to_rad_ps(cutoff_cm)
    return 2.0 * strength * cutoff * omega_ps_inv / (
        omega_ps_inv**2 + cutoff**2
    )


def derive_kappa(
    omega_ref: float,
    bath_strength_cm: float,
    cutoff_cm: float,
    temperature_k: float,
) -> float:
    """Compute dephasing rate kappa from Drude-Lorentz spectral density."""
    j_value = spectral_density_ps_inv(
        omega_ps_inv=omega_ref,
        bath_strength_cm=bath_strength_cm,
        cutoff_cm=cutoff_cm,
    )
    kappa = 2.0 * pi * j_value * thermal_weight(omega_ref, temperature_k)
    return kappa


# ---------------------------------------------------------------------------
# Liouvillian builders
# ---------------------------------------------------------------------------

def build_liouvillian(
    h: np.ndarray, kappa_ps_inv: float, coupling_matrix: np.ndarray
) -> np.ndarray:
    """Build Liouvillian superoperator with QSW transition Lindblad operators.

    Uses the Quantum Stochastic Walk model (Whitfield et al. 2010) with
    thermally-weighted detailed balance: for each pair of connected sites
    (i, j) with nonzero coupling C_ij, a transition operator
    L_{i<-j} = sqrt(rate_{i<-j}) |i><j| is added, where the rates satisfy
    detailed balance: rate(i<-j)/rate(j<-i) = exp(-(E_i - E_j)/(kT)).

    The site energies E_i are taken from the diagonal of the Hamiltonian h.
    Temperature is set to 310 K (physiological).
    """
    n = h.shape[0]
    ident = np.eye(n, dtype=np.complex128)
    liouvillian = -1j * (np.kron(ident, h) - np.kron(h.T, ident))

    # Site energies from diagonal of h (in rad/ps)
    site_energies = np.real(np.diag(h))

    # Thermal energy kT in rad/ps (at 310 K)
    temperature_k = 310.0
    kT = KB_OVER_HBAR_PS_K * temperature_k  # in rad/ps

    # Normalise coupling strengths so the strongest coupling has rate kappa
    abs_couplings = np.abs(coupling_matrix)
    max_coupling = np.max(abs_couplings)
    threshold = 1e-12

    if max_coupling > threshold:
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                c_ij = abs_couplings[i, j]
                if c_ij < threshold:
                    continue
                # Base rate from coupling topology
                base_rate = kappa_ps_inv * c_ij / max_coupling
                # Detailed balance: Boltzmann weight for transition j -> i
                # Lower energy i is favoured: rate(i<-j) ~ exp(-E_i/(2kT)) / exp(-E_j/(2kT))
                # Split the Boltzmann factor symmetrically between forward/reverse
                delta_E = site_energies[i] - site_energies[j]
                boltzmann_factor = np.exp(-delta_E / (2.0 * kT))
                rate = base_rate * boltzmann_factor
                # Transition operator L_{i<-j} = sqrt(rate) |i><j|
                lop = np.zeros((n, n), dtype=np.complex128)
                lop[i, j] = np.sqrt(rate)
                ld_l = lop.conj().T @ lop
                liouvillian += np.kron(lop.conj(), lop)
                liouvillian -= 0.5 * np.kron(ident, ld_l)
                liouvillian -= 0.5 * np.kron(ld_l.T, ident)

    return liouvillian


def build_liouvillian_with_sink(
    h: np.ndarray,
    kappa_ps_inv: float,
    coupling_matrix: np.ndarray,
    sink_site: int,
    sink_rate_ps_inv: float,
) -> np.ndarray:
    """Build Liouvillian with QSW transition operators plus irreversible trapping at sink_site.

    The sink is modelled as an irreversible decay channel that removes
    population from the system.  In the Lindblad master equation this
    corresponds to keeping only the anti-commutator (decay) part of a
    Lindblad dissipator and dropping the recycling (jump) term:

        d rho / dt |_sink = - (Gamma/2) { |s><s|, rho }

    In superoperator form this is:
        L_sink = - (Gamma/2) [ I kron |s><s|  +  |s><s|^T kron I ]

    This makes the generator non-trace-preserving: Tr(rho) decreases over
    time, and 1 - Tr(rho(t)) equals the population captured by the sink.
    """
    n = h.shape[0]
    ident = np.eye(n, dtype=np.complex128)

    # Start with QSW Liouvillian (coherent + classical hopping)
    liouvillian = build_liouvillian(h, kappa_ps_inv, coupling_matrix)

    # Sink: irreversible population decay from sink_site
    # Projector onto the sink site
    proj_sink = np.zeros((n, n), dtype=np.complex128)
    proj_sink[sink_site, sink_site] = 1.0

    # Anti-commutator part only (no recycling) -> population leaves the system
    liouvillian -= 0.5 * sink_rate_ps_inv * np.kron(ident, proj_sink)
    liouvillian -= 0.5 * sink_rate_ps_inv * np.kron(proj_sink.T, ident)

    return liouvillian


# ---------------------------------------------------------------------------
# Steady-state solver
# ---------------------------------------------------------------------------

def steady_state(liouvillian: np.ndarray, sites: int) -> np.ndarray:
    """
    Find the steady state of a Liouvillian by SVD.

    Returns the density matrix rho_ss such that L @ vec(rho_ss) = 0.
    """
    U, s, Vh = svd(liouvillian)
    # The right singular vector for the smallest singular value
    rho_vec = Vh[-1, :].conj()
    rho = rho_vec.reshape((sites, sites), order="F")
    # Symmetrise
    rho = 0.5 * (rho + rho.conj().T)
    # Normalise by trace
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("Steady-state density matrix has zero trace.")
    rho = rho / tr
    return rho
