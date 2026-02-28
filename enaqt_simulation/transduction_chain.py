"""
Transduction Chain Quantitative Viability Analysis
====================================================

The single most important calculation for NFT (Navigational Faculty Theory):
Is the radical pair spin coherence mechanism quantitatively viable for
real-time cognitive effects?

NFT proposes:
  Radical pair event → yield difference → tubulin conformation →
  microtubule state → ion channel / synapse → neural signal →
  criticality amplification → cognitive effect

This script estimates the signal-to-noise ratio at each step of this
transduction chain, using conservative (less favorable) parameter estimates.

References cited inline. All values at T = 310 K unless otherwise noted.

Author: Kenneth Malloy / NFT Project
Date: 2026-03-15
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# =============================================================================
# Physical constants
# =============================================================================

K_B = 1.381e-23         # Boltzmann constant, J/K
T_BODY = 310.0           # physiological temperature, K
KT = K_B * T_BODY        # thermal energy at 310K, J (~4.28e-21 J)
N_A = 6.022e23           # Avogadro's number, mol^-1
E_CHARGE = 1.602e-19     # elementary charge, C


# =============================================================================
# Step 1: Radical pair event rate
# =============================================================================

def step1_radical_pair_rate(
    D_O2: float = 1.0e-9,       # m^2/s, diffusion coeff of O2^- in cytoplasm
                                  # Ref: Takahashi et al. 1999, ~1-2e-9 m^2/s
                                  # Using conservative lower bound
    r_encounter: float = 0.5e-9,  # m, encounter radius for Trp + O2^-
                                  # Ref: typical van der Waals contact ~0.3-0.5 nm
                                  # Conservative: 0.5 nm
    c_ROS_nM: float = 1.0,       # nM, baseline ROS (superoxide) concentration
                                  # Ref: Sies & Jones 2020, steady-state O2^- ~1-10 nM
                                  # Conservative: 1 nM (baseline, not during activity)
    n_trp_per_dimer: int = 8,     # tryptophan residues per tubulin dimer
                                  # Ref: Löwe et al. 2001 (tubulin structure)
                                  # 4 per alpha-tubulin + 4 per beta-tubulin
    p_accessible: float = 0.5,    # fraction of Trp residues solvent-accessible
                                  # Conservative: only half are accessible to O2^-
                                  # Ref: structural analysis, surface Trp fraction varies
) -> Dict:
    """
    Estimate radical pair formation rate per tubulin dimer.

    Uses Smoluchowski diffusion-limited encounter rate:
      k_enc = 4 * pi * D * r * N_A  (M^-1 s^-1)

    Then rate per Trp site:
      rate_per_site = k_enc * [O2^-]

    And rate per dimer:
      rate_per_dimer = n_accessible_trp * rate_per_site
    """

    # Smoluchowski diffusion-limited rate constant
    # k = 4 * pi * D * r * N_A  (in M^-1 s^-1)
    # Ref: Smoluchowski 1917; standard physical chemistry
    k_enc = 4 * np.pi * D_O2 * r_encounter * N_A  # M^-1 s^-1

    # Convert ROS concentration to M
    c_ROS_M = c_ROS_nM * 1e-9  # M

    # Rate per accessible tryptophan site
    rate_per_site = k_enc * c_ROS_M  # s^-1

    # Number of accessible tryptophan sites per dimer
    n_accessible = n_trp_per_dimer * p_accessible

    # Rate per tubulin dimer
    rate_per_dimer = n_accessible * rate_per_site  # s^-1

    # Convert to events per millisecond
    rate_per_dimer_per_ms = rate_per_dimer * 1e-3

    # Not all encounters produce a radical pair. The superoxide must
    # actually abstract an electron from Trp. Efficiency is uncertain.
    # Ref: Forni et al. 2016, radical formation yield ~1-10% for
    # O2^- + amino acid reactions. Use conservative 1%.
    p_radical_formation = 0.01

    effective_rate_per_dimer = rate_per_dimer * p_radical_formation  # s^-1
    effective_rate_per_dimer_per_ms = effective_rate_per_dimer * 1e-3

    return {
        'k_enc_M_per_s': k_enc,
        'c_ROS_M': c_ROS_M,
        'rate_per_site_s': rate_per_site,
        'n_accessible': n_accessible,
        'rate_per_dimer_s': rate_per_dimer,
        'rate_per_dimer_per_ms': rate_per_dimer_per_ms,
        'p_radical_formation': p_radical_formation,
        'effective_rate_per_dimer_s': effective_rate_per_dimer,
        'effective_rate_per_dimer_per_ms': effective_rate_per_dimer_per_ms,
        'D_O2': D_O2,
        'r_encounter': r_encounter,
        'c_ROS_nM': c_ROS_nM,
        'n_trp_per_dimer': n_trp_per_dimer,
        'p_accessible': p_accessible,
    }


# =============================================================================
# Step 2: Signal per event (differential yield)
# =============================================================================

def step2_signal_per_event(
    yield_difference: float = 0.127,    # 12.7% quantum-classical yield difference
                                         # From spin_coherence.py simulation at 310K
    conformational_energy_kT: float = 1.0,
                                         # Free energy difference between tubulin
                                         # conformational states, in units of kT
                                         # Ref: Dima & Joshi 2008, ~1-10 kT for
                                         # major conformational changes; GTP hydrolysis
                                         # releases ~8 kT but coupled to other processes.
                                         # For a subtle shift (not full straight->curved),
                                         # conservative: 1 kT
) -> Dict:
    """
    Estimate the signal produced by a single radical pair event.

    The 12.7% yield difference means: quantum dynamics shifts the singlet
    product fraction by 12.7% relative to classical.

    This differential product then drives a conformational bias.
    The key question: how much conformational "force" does one
    differential chemical product exert, compared to thermal noise?
    """

    # Energy of conformational change
    E_conform = conformational_energy_kT * KT  # Joules

    # The differential energy per event:
    # One event produces either singlet or triplet product.
    # The quantum mechanism shifts the probability by yield_difference.
    # So the EXPECTED differential energy per event is:
    #   delta_E = yield_difference * E_conform
    # This is the bias toward one conformational state per event.
    delta_E_per_event = yield_difference * E_conform  # J

    # Compare to thermal noise per event
    # Each event produces a kick of either +E_conform or 0
    # (singlet product promotes conformational change, triplet does not)
    # The thermal noise is just kT (the scale of random fluctuations)
    SNR_single_event = delta_E_per_event / KT

    # Force interpretation:
    # Typical conformational displacement: ~0.1-1 nm
    # Ref: tubulin lateral contacts shift ~0.2-0.5 nm between states
    # Conservative: 0.5 nm
    d_conform = 0.5e-9  # m

    # Differential force per event
    F_diff = delta_E_per_event / d_conform  # N

    # Thermal force scale: sqrt(2 * k_B * T * gamma / dt)
    # But for order-of-magnitude, just kT/d
    F_thermal = KT / d_conform  # N

    # Force SNR per event
    SNR_force = F_diff / F_thermal

    return {
        'yield_difference': yield_difference,
        'conformational_energy_kT': conformational_energy_kT,
        'E_conform_J': E_conform,
        'delta_E_per_event_J': delta_E_per_event,
        'delta_E_per_event_kT': delta_E_per_event / KT,
        'SNR_single_event': SNR_single_event,
        'd_conform_nm': d_conform * 1e9,
        'F_diff_pN': F_diff * 1e12,
        'F_thermal_pN': F_thermal * 1e12,
        'SNR_force': SNR_force,
    }


# =============================================================================
# Step 3: Aggregate at microtubule level
# =============================================================================

def step3_microtubule_aggregate(
    step1: Dict,
    step2: Dict,
    n_protofilaments: int = 13,        # standard MT has 13 protofilaments
    dimers_per_protofilament: int = 1000,  # ~8 nm per dimer, ~8 um per 1000 dimers
                                           # Typical MT length: 1-25 um
                                           # Conservative: use shorter MT
    t_neural_ms: float = 5.0,          # neural integration timescale, ms
                                        # Ref: EPSP rise time ~1-5 ms
                                        # Use 5 ms as integration window
) -> Dict:
    """
    Aggregate radical pair signal across a microtubule.

    Key question: does the aggregate signal exceed sqrt(N) thermal noise?
    """

    # Total dimers per MT
    N_dimers = n_protofilaments * dimers_per_protofilament

    # Total radical pair events per MT per neural timescale
    events_per_MT = (step1['effective_rate_per_dimer_s']
                     * N_dimers
                     * t_neural_ms * 1e-3)

    # Total signal: sum of N_events independent biased events
    # Each event contributes delta_E with probability given by yield_difference
    # Expected total signal:
    total_signal_J = events_per_MT * step2['delta_E_per_event_J']
    total_signal_kT = total_signal_J / KT

    # Thermal noise at the MT level:
    # Each dimer experiences thermal fluctuations of order kT
    # Over the neural timescale, the relevant noise is:
    #   - Each event has noise of order kT (the conformational energy scale)
    #   - N_events independent noise sources
    #   - Total noise = sqrt(N_events) * kT
    # This is the signal-detection-theory framework:
    #   SNR = N_events * delta / (sqrt(N_events) * sigma)
    #       = sqrt(N_events) * delta/sigma
    # where delta = delta_E_per_event, sigma = kT

    if events_per_MT > 0:
        noise_kT = np.sqrt(events_per_MT)  # in units of kT
        SNR_MT = total_signal_kT / noise_kT
        # Equivalently: SNR = sqrt(N) * (delta_E / kT)
        SNR_MT_check = np.sqrt(events_per_MT) * step2['SNR_single_event']
    else:
        noise_kT = 0
        SNR_MT = 0
        SNR_MT_check = 0

    # But there is a SECOND noise source: dimers that are NOT undergoing
    # radical pair events are ALSO fluctuating thermally.
    # The question is whether the signal dimers can be distinguished
    # from the thermal background of ALL dimers.

    # Total thermal noise from all dimers (not just event dimers):
    # N_dimers dimers each fluctuating at kT
    # Over timescale t, if each dimer has a relaxation time tau_relax,
    # it undergoes t/tau_relax independent fluctuations.
    # Tubulin conformational relaxation: ~100 ns - 1 us
    # Ref: molecular dynamics estimates, Ayoub et al. 2015
    tau_relax_us = 0.1  # us = 100 ns, conservative (fast relaxation = more noise)
    tau_relax_s = tau_relax_us * 1e-6

    n_fluctuations_per_dimer = (t_neural_ms * 1e-3) / tau_relax_s
    total_noise_fluctuations = N_dimers * n_fluctuations_per_dimer
    total_background_noise_kT = np.sqrt(total_noise_fluctuations)

    SNR_MT_vs_background = total_signal_kT / total_background_noise_kT

    return {
        'N_dimers': N_dimers,
        'n_protofilaments': n_protofilaments,
        'dimers_per_protofilament': dimers_per_protofilament,
        't_neural_ms': t_neural_ms,
        'events_per_MT': events_per_MT,
        'total_signal_kT': total_signal_kT,
        'noise_kT': noise_kT,
        'SNR_MT': SNR_MT,
        'SNR_MT_check': SNR_MT_check,
        'tau_relax_us': tau_relax_us,
        'n_fluctuations_per_dimer': n_fluctuations_per_dimer,
        'total_background_noise_kT': total_background_noise_kT,
        'SNR_MT_vs_background': SNR_MT_vs_background,
    }


# =============================================================================
# Step 4: Aggregate at neuron level
# =============================================================================

def step4_neuron_aggregate(
    step3: Dict,
    n_MT_per_neuron: int = 1000,       # total microtubules per neuron
                                        # Ref: Heidemann 1996, typical neuron has
                                        # ~100 MTs in axon, ~10-100 per dendrite
                                        # Total: ~1000-10000
                                        # Conservative: 1000
    tubulin_dimers_per_neuron: float = 1e9,  # "one billion" from manuscript
                                              # Check: 1000 MTs * 13000 dimers = 13e6
                                              # That is 13 million, NOT 1 billion.
                                              # 1 billion requires ~77,000 MTs or
                                              # ~77 um average MT length at 13000 dimers/MT
                                              # This is high but not impossible for a
                                              # large pyramidal neuron with extensive
                                              # dendritic arbor. Each dendrite can be
                                              # hundreds of um long.
                                              # Alternative: Bhatt et al. 2009 estimates
                                              # ~10^9 tubulin dimers in cortical pyramidal neurons
) -> Dict:
    """
    Aggregate signal across all microtubules in a neuron.
    """

    # Check consistency of dimer count
    dimers_from_MT_count = n_MT_per_neuron * step3['N_dimers']

    # Use the more conservative number (smaller)
    # The MT count gives 13 million; the manuscript says 1 billion
    # The discrepancy suggests either more MTs or longer MTs than assumed.
    # For conservatism, use the smaller number (from MT count).
    effective_dimers = dimers_from_MT_count

    # Total events per neuron per neural timescale
    events_per_neuron = n_MT_per_neuron * step3['events_per_MT']

    # Total signal
    total_signal_kT = n_MT_per_neuron * step3['total_signal_kT']

    # Noise: independent MTs contribute independent noise
    # Total noise = sqrt(N_MT) * noise_per_MT (if noise is from events)
    # But more properly: total events across neuron, sqrt(N_events_total)
    if events_per_neuron > 0:
        noise_events_kT = np.sqrt(events_per_neuron)
        SNR_neuron_events = total_signal_kT / noise_events_kT
    else:
        noise_events_kT = 0
        SNR_neuron_events = 0

    # Background noise from all dimers
    total_background_noise_kT = (np.sqrt(n_MT_per_neuron)
                                  * step3['total_background_noise_kT'])
    SNR_neuron_background = total_signal_kT / total_background_noise_kT

    # Convert signal to physically meaningful units
    # Can this signal change an ion channel?
    # Ion channel gating energy: ~5-15 kT
    # Ref: Hille 2001, Ion Channels of Excitable Membranes
    # We need the aggregate signal to produce at least ~1 kT bias
    # at a specific channel location.

    # But the signal is distributed across the whole neuron.
    # The fraction that reaches any one channel depends on how
    # the signal propagates through the cytoskeleton.

    # If MTs couple to MAP2/tau which couple to ion channels:
    # Signal at one channel ~ total signal / N_channels_coupled
    # N_channels per neuron: ~10,000-100,000
    # Ref: typical cortical pyramidal neuron
    n_channels = 10000  # conservative low estimate
    signal_per_channel_kT = total_signal_kT / n_channels

    return {
        'n_MT_per_neuron': n_MT_per_neuron,
        'dimers_from_MT_count': dimers_from_MT_count,
        'tubulin_dimers_per_neuron_claimed': tubulin_dimers_per_neuron,
        'effective_dimers': effective_dimers,
        'events_per_neuron': events_per_neuron,
        'total_signal_kT': total_signal_kT,
        'noise_events_kT': noise_events_kT,
        'SNR_neuron_events': SNR_neuron_events,
        'total_background_noise_kT': total_background_noise_kT,
        'SNR_neuron_background': SNR_neuron_background,
        'n_channels': n_channels,
        'signal_per_channel_kT': signal_per_channel_kT,
    }


# =============================================================================
# Step 5: Criticality amplification
# =============================================================================

def step5_criticality(
    step4: Dict,
    amplification_factor: float = 51.0,   # from criticality_amplification.py
                                            # 0.2% bias → 10.2% effect
                                            # Factor = 10.2 / 0.2 = 51x
                                            # Note: this is for a specific model
                                            # (N=1000 branching network)
) -> Dict:
    """
    Apply criticality amplification to the neural signal.

    IMPORTANT CAVEAT: The 51x factor was computed for a specific model where
    the "bias" was applied as a perturbation to the firing probability.
    Here, the "bias" would need to translate into a firing probability
    change. This is the weakest link in the chain.
    """

    # The signal reaching ion channels must translate into a
    # probability bias for neural firing.
    # A typical synaptic event shifts Vm by ~0.5-1 mV
    # (Ref: Magee 2000, dendritic integration)
    # The threshold for firing is ~15-20 mV above rest
    # So one synapse contributes ~1/20 to 1/40 of threshold

    # Can the radical pair signal create an equivalent bias?
    # The signal per channel is in kT units.
    # Ion channel gating: open probability depends on Vm as
    #   P_open ~ 1 / (1 + exp(-z*e*V/(kT)))
    # where z is effective gating charge (~4 for Na+ channels)
    # Ref: Bezanilla 2000, voltage gating mechanisms

    # A perturbation of delta_E (in kT) at the channel changes P_open by:
    #   delta_P ~ P_open * (1 - P_open) * z * delta_E
    # At rest, P_open ~ 0.01 for Na+ channels (mostly closed)
    # So delta_P ~ 0.01 * 0.99 * 4 * delta_E ~ 0.04 * delta_E

    z_gating = 4.0  # effective gating charges
    P_open_rest = 0.01  # resting open probability
    delta_E_channel = step4['signal_per_channel_kT']  # kT per channel

    delta_P_open = P_open_rest * (1 - P_open_rest) * z_gating * delta_E_channel

    # This delta_P_open across N_channels produces a current change:
    # delta_I = N_channels * delta_P_open * i_single
    # where i_single is single-channel current (~1-5 pA for Na+)
    # Ref: Hille 2001
    i_single_pA = 2.0  # pA
    n_channels = step4['n_channels']
    delta_I_pA = n_channels * delta_P_open * i_single_pA
    delta_I_pA_total = delta_I_pA  # pA

    # Convert to voltage change using input resistance
    # Typical input resistance: 50-200 MOhm for cortical pyramidal neurons
    # Ref: Spruston 2008
    R_input_MOhm = 100.0  # MOhm
    delta_V_mV = delta_I_pA_total * 1e-12 * R_input_MOhm * 1e6 * 1e3  # mV

    # Compare to synaptic potential and neural noise
    V_synapse_mV = 0.5  # typical EPSP amplitude, mV
    V_noise_mV = 0.1    # neural voltage noise, mV (thermal Johnson noise)
                          # Ref: Faisal et al. 2008, noise in the nervous system

    # Fractional bias on firing probability
    # (how much the radical pair signal shifts firing probability)
    # Firing threshold: ~15-20 mV; each mV contributes ~5-7% to threshold
    V_threshold_mV = 15.0
    firing_prob_bias = delta_V_mV / V_threshold_mV

    # Now apply criticality amplification
    amplified_bias = firing_prob_bias * amplification_factor

    # But wait: the criticality amplification was measured for a bias
    # applied to the firing probability, not voltage. The conversion
    # is: delta_p_fire ~ delta_V / V_threshold for small delta_V.
    # So the amplified effect on network-level behavior is:
    amplified_effect = amplified_bias

    return {
        'amplification_factor': amplification_factor,
        'z_gating': z_gating,
        'P_open_rest': P_open_rest,
        'delta_E_channel_kT': delta_E_channel,
        'delta_P_open': delta_P_open,
        'i_single_pA': i_single_pA,
        'delta_I_pA': delta_I_pA_total,
        'R_input_MOhm': R_input_MOhm,
        'delta_V_mV': delta_V_mV,
        'V_synapse_mV': V_synapse_mV,
        'V_noise_mV': V_noise_mV,
        'V_threshold_mV': V_threshold_mV,
        'firing_prob_bias': firing_prob_bias,
        'amplified_bias': amplified_bias,
    }


# =============================================================================
# Step 6: Compare to known neural signals
# =============================================================================

def step6_comparison(step5: Dict) -> Dict:
    """
    Compare the transduced quantum signal to known neural signal scales.
    """

    # Known signal scales:
    signals = {
        'EPSP (single synapse)': 0.5,        # mV
        'Neural voltage noise (thermal)': 0.1, # mV
        'Ion channel stochasticity': 0.05,     # mV, Ref: White et al. 2000
        'Stochastic resonance threshold': 0.01, # mV (approximate)
        'Action potential threshold above rest': 15.0,  # mV
    }

    delta_V = step5['delta_V_mV']

    # Ratios
    ratios = {}
    for name, v in signals.items():
        ratios[name] = delta_V / v

    # Overall verdict
    # The key question: is delta_V comparable to or larger than
    # the stochastic resonance threshold?
    # In stochastic resonance, a weak subthreshold signal can be
    # detected if it is above ~1/10 of the noise level.
    # Ref: Gammaitoni et al. 1998, stochastic resonance

    stochastic_resonance_detectable = delta_V > 0.01  # crude threshold
    exceeds_thermal_noise = delta_V > 0.1
    exceeds_channel_noise = delta_V > 0.05

    return {
        'delta_V_mV': delta_V,
        'amplified_bias': step5['amplified_bias'],
        'signal_scales': signals,
        'ratios': ratios,
        'stochastic_resonance_detectable': stochastic_resonance_detectable,
        'exceeds_thermal_noise': exceeds_thermal_noise,
        'exceeds_channel_noise': exceeds_channel_noise,
    }


# =============================================================================
# Parameter sensitivity analysis
# =============================================================================

def sensitivity_analysis() -> Dict:
    """
    Test how the overall SNR depends on key parameters.
    """

    # Baseline
    s1_base = step1_radical_pair_rate()
    s2_base = step2_signal_per_event()
    s3_base = step3_microtubule_aggregate(s1_base, s2_base)
    s4_base = step4_neuron_aggregate(s3_base)
    s5_base = step5_criticality(s4_base)

    baseline_V = s5_base['delta_V_mV']
    baseline_bias = s5_base['amplified_bias']

    results = {}

    # Vary ROS concentration
    ros_values = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]
    ros_results = []
    for ros in ros_values:
        s1 = step1_radical_pair_rate(c_ROS_nM=ros)
        s2 = step2_signal_per_event()
        s3 = step3_microtubule_aggregate(s1, s2)
        s4 = step4_neuron_aggregate(s3)
        s5 = step5_criticality(s4)
        ros_results.append({
            'c_ROS_nM': ros,
            'delta_V_mV': s5['delta_V_mV'],
            'amplified_bias': s5['amplified_bias'],
            'events_per_neuron': s4['events_per_neuron'],
        })
    results['ROS_concentration'] = ros_results

    # Vary number of MTs per neuron
    mt_values = [100, 500, 1000, 5000, 10000, 50000, 77000]
    mt_results = []
    for n_mt in mt_values:
        s1 = step1_radical_pair_rate()
        s2 = step2_signal_per_event()
        s3 = step3_microtubule_aggregate(s1, s2)
        s4 = step4_neuron_aggregate(s3, n_MT_per_neuron=n_mt)
        s5 = step5_criticality(s4)
        mt_results.append({
            'n_MT': n_mt,
            'delta_V_mV': s5['delta_V_mV'],
            'amplified_bias': s5['amplified_bias'],
            'events_per_neuron': s4['events_per_neuron'],
            'total_dimers': n_mt * s3['N_dimers'],
        })
    results['MT_count'] = mt_results

    # Vary encounter radius
    r_values = [0.3e-9, 0.5e-9, 1.0e-9, 2.0e-9, 5.0e-9]
    r_results = []
    for r in r_values:
        s1 = step1_radical_pair_rate(r_encounter=r)
        s2 = step2_signal_per_event()
        s3 = step3_microtubule_aggregate(s1, s2)
        s4 = step4_neuron_aggregate(s3)
        s5 = step5_criticality(s4)
        r_results.append({
            'r_nm': r * 1e9,
            'delta_V_mV': s5['delta_V_mV'],
            'amplified_bias': s5['amplified_bias'],
        })
    results['encounter_radius'] = r_results

    # Vary conformational energy
    ce_values = [0.1, 0.5, 1.0, 5.0, 10.0]
    ce_results = []
    for ce in ce_values:
        s1 = step1_radical_pair_rate()
        s2 = step2_signal_per_event(conformational_energy_kT=ce)
        s3 = step3_microtubule_aggregate(s1, s2)
        s4 = step4_neuron_aggregate(s3)
        s5 = step5_criticality(s4)
        ce_results.append({
            'E_conform_kT': ce,
            'delta_V_mV': s5['delta_V_mV'],
            'amplified_bias': s5['amplified_bias'],
        })
    results['conformational_energy'] = ce_results

    # Vary radical formation probability
    prf_values = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    prf_results = []
    for prf in prf_values:
        s1 = step1_radical_pair_rate()
        # Override the radical formation probability
        s1['effective_rate_per_dimer_s'] = s1['rate_per_dimer_s'] * prf
        s1['effective_rate_per_dimer_per_ms'] = s1['effective_rate_per_dimer_s'] * 1e-3
        s2 = step2_signal_per_event()
        s3 = step3_microtubule_aggregate(s1, s2)
        s4 = step4_neuron_aggregate(s3)
        s5 = step5_criticality(s4)
        prf_results.append({
            'p_radical_formation': prf,
            'delta_V_mV': s5['delta_V_mV'],
            'amplified_bias': s5['amplified_bias'],
            'events_per_neuron': s4['events_per_neuron'],
        })
    results['radical_formation_prob'] = prf_results

    # Combined optimistic scenario
    s1_opt = step1_radical_pair_rate(c_ROS_nM=10.0, r_encounter=1.0e-9)
    s1_opt['effective_rate_per_dimer_s'] = s1_opt['rate_per_dimer_s'] * 0.05
    s1_opt['effective_rate_per_dimer_per_ms'] = s1_opt['effective_rate_per_dimer_s'] * 1e-3
    s2_opt = step2_signal_per_event(conformational_energy_kT=5.0)
    s3_opt = step3_microtubule_aggregate(s1_opt, s2_opt)
    s4_opt = step4_neuron_aggregate(s3_opt, n_MT_per_neuron=10000)
    s5_opt = step5_criticality(s4_opt)
    results['optimistic'] = {
        'delta_V_mV': s5_opt['delta_V_mV'],
        'amplified_bias': s5_opt['amplified_bias'],
        'events_per_neuron': s4_opt['events_per_neuron'],
        'params': 'ROS=10nM, r=1nm, p_rad=5%, E_conf=5kT, N_MT=10000',
    }

    # Combined pessimistic scenario
    s1_pes = step1_radical_pair_rate(c_ROS_nM=0.5, r_encounter=0.3e-9)
    s1_pes['effective_rate_per_dimer_s'] = s1_pes['rate_per_dimer_s'] * 0.001
    s1_pes['effective_rate_per_dimer_per_ms'] = s1_pes['effective_rate_per_dimer_s'] * 1e-3
    s2_pes = step2_signal_per_event(conformational_energy_kT=0.5)
    s3_pes = step3_microtubule_aggregate(s1_pes, s2_pes)
    s4_pes = step4_neuron_aggregate(s3_pes, n_MT_per_neuron=500)
    s5_pes = step5_criticality(s4_pes)
    results['pessimistic'] = {
        'delta_V_mV': s5_pes['delta_V_mV'],
        'amplified_bias': s5_pes['amplified_bias'],
        'events_per_neuron': s4_pes['events_per_neuron'],
        'params': 'ROS=0.5nM, r=0.3nm, p_rad=0.1%, E_conf=0.5kT, N_MT=500',
    }

    return results


# =============================================================================
# Main: run everything and print results
# =============================================================================

def main():
    print("=" * 90)
    print("  TRANSDUCTION CHAIN QUANTITATIVE VIABILITY ANALYSIS")
    print("  Radical Pair Spin Coherence -> Cognitive Effect")
    print("  NFT (Navigational Faculty Theory) -- Critical Calculation")
    print("=" * 90)
    print()
    print(f"  Temperature: {T_BODY} K")
    print(f"  kT = {KT:.3e} J = {KT*1e21:.2f} zJ = {KT/(1e-12 * 1e-9):.2f} pN*nm")
    print()

    # =========================================================================
    # Step 1: Radical pair event rate
    # =========================================================================
    print("=" * 90)
    print("  STEP 1: RADICAL PAIR EVENT RATE")
    print("=" * 90)

    s1 = step1_radical_pair_rate()

    print(f"""
  Parameters (conservative):
    D(O2^-) in cytoplasm:        {s1['D_O2']:.1e} m^2/s
    Encounter radius:            {s1['r_encounter']*1e9:.1f} nm
    [O2^-] (baseline ROS):       {s1['c_ROS_nM']:.1f} nM
    Trp residues per dimer:      {s1['n_trp_per_dimer']}
    Fraction accessible:         {s1['p_accessible']:.1%}
    Radical formation prob:      {s1['p_radical_formation']:.1%}

  Results:
    Smoluchowski rate constant:  {s1['k_enc_M_per_s']:.3e} M^-1 s^-1
    Encounter rate per site:     {s1['rate_per_site_s']:.3e} s^-1
    Encounter rate per dimer:    {s1['rate_per_dimer_s']:.3e} s^-1
    Effective RP rate per dimer: {s1['effective_rate_per_dimer_s']:.3e} s^-1
    Effective RP per dimer/ms:   {s1['effective_rate_per_dimer_per_ms']:.3e}

  Interpretation:
    At baseline ROS, each tubulin dimer experiences ~{s1['effective_rate_per_dimer_s']:.1e} radical
    pair events per second, or ~{s1['effective_rate_per_dimer_per_ms']:.1e} per millisecond.
    This is a VERY LOW rate per dimer -- but there are many dimers.
""")

    # =========================================================================
    # Step 2: Signal per event
    # =========================================================================
    print("=" * 90)
    print("  STEP 2: SIGNAL PER RADICAL PAIR EVENT")
    print("=" * 90)

    s2 = step2_signal_per_event()

    print(f"""
  Parameters:
    Quantum-classical yield diff:  {s2['yield_difference']*100:.1f}%
    Conformational energy:         {s2['conformational_energy_kT']:.1f} kT = {s2['E_conform_J']:.3e} J
    Conformational displacement:   {s2['d_conform_nm']:.1f} nm

  Results:
    Differential energy per event: {s2['delta_E_per_event_kT']:.4f} kT = {s2['delta_E_per_event_J']:.3e} J
    SNR per single event:          {s2['SNR_single_event']:.4f}
    Differential force:            {s2['F_diff_pN']:.4f} pN
    Thermal force scale:           {s2['F_thermal_pN']:.2f} pN

  Interpretation:
    Each radical pair event produces a conformational bias of {s2['delta_E_per_event_kT']:.3f} kT.
    This is FAR below thermal noise (kT). A single event is completely invisible
    against thermal fluctuations. The theory requires statistical aggregation.
""")

    # =========================================================================
    # Step 3: Microtubule aggregate
    # =========================================================================
    print("=" * 90)
    print("  STEP 3: AGGREGATION AT MICROTUBULE LEVEL")
    print("=" * 90)

    s3 = step3_microtubule_aggregate(s1, s2)

    print(f"""
  Parameters:
    Protofilaments:              {s3['n_protofilaments']}
    Dimers per protofilament:    {s3['dimers_per_protofilament']}
    Total dimers per MT:         {s3['N_dimers']:,}
    Neural integration time:     {s3['t_neural_ms']:.1f} ms

  Results:
    RP events per MT per {s3['t_neural_ms']} ms:    {s3['events_per_MT']:.3e}
    Total signal per MT:         {s3['total_signal_kT']:.3e} kT
    Noise (from events):         {s3['noise_kT']:.3e} kT
    SNR (event noise only):      {s3['SNR_MT']:.3e}

    Tubulin relaxation time:     {s3['tau_relax_us']:.1f} us
    Fluctuations per dimer:      {s3['n_fluctuations_per_dimer']:.1e}
    Total background noise:      {s3['total_background_noise_kT']:.1e} kT
    SNR (vs all background):     {s3['SNR_MT_vs_background']:.3e}

  Interpretation:
    A single microtubule has ~{s3['events_per_MT']:.1e} radical pair events in {s3['t_neural_ms']} ms.
    The signal is {s3['total_signal_kT']:.2e} kT, overwhelmed by background noise
    of {s3['total_background_noise_kT']:.1e} kT. SNR << 1 at the single-MT level.
""")

    # =========================================================================
    # Step 4: Neuron aggregate
    # =========================================================================
    print("=" * 90)
    print("  STEP 4: AGGREGATION AT NEURON LEVEL")
    print("=" * 90)

    s4 = step4_neuron_aggregate(s3)

    print(f"""
  Parameters:
    Microtubules per neuron:     {s4['n_MT_per_neuron']:,}
    Total dimers (from MTs):     {s4['dimers_from_MT_count']:,.0f}
    Manuscript claim:            {s4['tubulin_dimers_per_neuron_claimed']:.0e}
    (Using conservative estimate from MT count)

  Results:
    RP events per neuron per {s3['t_neural_ms']} ms: {s4['events_per_neuron']:.3e}
    Total signal:                {s4['total_signal_kT']:.3e} kT
    Event-based noise:           {s4['noise_events_kT']:.3e} kT
    SNR (event noise):           {s4['SNR_neuron_events']:.3e}
    Background noise:            {s4['total_background_noise_kT']:.3e} kT
    SNR (vs background):        {s4['SNR_neuron_background']:.3e}

    Ion channels per neuron:     {s4['n_channels']:,}
    Signal per channel:          {s4['signal_per_channel_kT']:.3e} kT

  Interpretation:
    Even aggregating {s4['n_MT_per_neuron']:,} MTs, the signal reaching each ion
    channel is {s4['signal_per_channel_kT']:.2e} kT -- still far below the gating
    energy of ion channels (~5-15 kT).
""")

    # =========================================================================
    # Step 5: Criticality amplification
    # =========================================================================
    print("=" * 90)
    print("  STEP 5: CRITICALITY AMPLIFICATION")
    print("=" * 90)

    s5 = step5_criticality(s4)

    print(f"""
  Parameters:
    Amplification factor:        {s5['amplification_factor']}x (from simulation)
    Gating charge z:             {s5['z_gating']}
    Resting P_open:              {s5['P_open_rest']}
    Single-channel current:      {s5['i_single_pA']:.1f} pA
    Input resistance:            {s5['R_input_MOhm']:.0f} MOhm

  Transduction to voltage:
    Energy perturbation/channel: {s5['delta_E_channel_kT']:.3e} kT
    Change in P_open:            {s5['delta_P_open']:.3e}
    Current change:              {s5['delta_I_pA']:.3e} pA
    Voltage change:              {s5['delta_V_mV']:.3e} mV

  Compare to neural signals:
    Typical EPSP:                {s5['V_synapse_mV']:.1f} mV
    Neural voltage noise:        {s5['V_noise_mV']:.1f} mV
    Firing threshold:            {s5['V_threshold_mV']:.0f} mV

  Firing probability bias:      {s5['firing_prob_bias']:.3e}
  After 51x amplification:      {s5['amplified_bias']:.3e}
""")

    # =========================================================================
    # Step 6: Final comparison
    # =========================================================================
    print("=" * 90)
    print("  STEP 6: COMPARISON TO KNOWN NEURAL SIGNALS")
    print("=" * 90)

    s6 = step6_comparison(s5)

    print(f"\n  Quantum-induced voltage change: {s6['delta_V_mV']:.3e} mV")
    print()
    print(f"  {'Signal scale':<45s} {'Value (mV)':>12s} {'Ratio':>14s}")
    print(f"  {'-'*72}")
    for name, v in s6['signal_scales'].items():
        ratio = s6['ratios'][name]
        print(f"  {name:<45s} {v:>12.4f} {ratio:>14.3e}")

    print(f"""
  Exceeds thermal noise?           {'YES' if s6['exceeds_thermal_noise'] else 'NO'}
  Exceeds channel stochasticity?   {'YES' if s6['exceeds_channel_noise'] else 'NO'}
  Detectable via stochastic res.?  {'YES' if s6['stochastic_resonance_detectable'] else 'NO'}
""")

    # =========================================================================
    # Sensitivity analysis
    # =========================================================================
    print("=" * 90)
    print("  PARAMETER SENSITIVITY ANALYSIS")
    print("=" * 90)

    sens = sensitivity_analysis()

    # ROS concentration
    print(f"\n  ROS Concentration Sensitivity:")
    print(f"  {'[O2^-] (nM)':>12s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s} {'Events/neuron':>14s}")
    print(f"  {'-'*56}")
    for r in sens['ROS_concentration']:
        print(f"  {r['c_ROS_nM']:>12.1f} {r['delta_V_mV']:>14.3e} {r['amplified_bias']:>14.3e} {r['events_per_neuron']:>14.3e}")

    # MT count
    print(f"\n  Microtubule Count Sensitivity:")
    print(f"  {'N_MT':>12s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s} {'Total dimers':>14s}")
    print(f"  {'-'*56}")
    for r in sens['MT_count']:
        print(f"  {r['n_MT']:>12,} {r['delta_V_mV']:>14.3e} {r['amplified_bias']:>14.3e} {r['total_dimers']:>14,.0f}")

    # Encounter radius
    print(f"\n  Encounter Radius Sensitivity:")
    print(f"  {'r (nm)':>12s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s}")
    print(f"  {'-'*42}")
    for r in sens['encounter_radius']:
        print(f"  {r['r_nm']:>12.1f} {r['delta_V_mV']:>14.3e} {r['amplified_bias']:>14.3e}")

    # Conformational energy
    print(f"\n  Conformational Energy Sensitivity:")
    print(f"  {'E_conf (kT)':>12s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s}")
    print(f"  {'-'*42}")
    for r in sens['conformational_energy']:
        print(f"  {r['E_conform_kT']:>12.1f} {r['delta_V_mV']:>14.3e} {r['amplified_bias']:>14.3e}")

    # Radical formation probability
    print(f"\n  Radical Formation Probability Sensitivity:")
    print(f"  {'p_rad':>12s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s} {'Events/neuron':>14s}")
    print(f"  {'-'*56}")
    for r in sens['radical_formation_prob']:
        print(f"  {r['p_radical_formation']:>12.3f} {r['delta_V_mV']:>14.3e} {r['amplified_bias']:>14.3e} {r['events_per_neuron']:>14.3e}")

    # Scenarios
    print(f"\n  Combined Scenarios:")
    opt = sens['optimistic']
    pes = sens['pessimistic']
    print(f"  {'Scenario':<14s} {'delta_V (mV)':>14s} {'Ampl. bias':>14s} {'Events/neuron':>14s}")
    print(f"  {'-'*58}")
    print(f"  {'Conservative':<14s} {s5['delta_V_mV']:>14.3e} {s5['amplified_bias']:>14.3e} {s4['events_per_neuron']:>14.3e}")
    print(f"  {'Optimistic':<14s} {opt['delta_V_mV']:>14.3e} {opt['amplified_bias']:>14.3e} {opt['events_per_neuron']:>14.3e}")
    print(f"  {'Pessimistic':<14s} {pes['delta_V_mV']:>14.3e} {pes['amplified_bias']:>14.3e} {pes['events_per_neuron']:>14.3e}")
    print()
    print(f"  Optimistic params:  {opt['params']}")
    print(f"  Pessimistic params: {pes['params']}")

    # =========================================================================
    # Orders of magnitude gap analysis
    # =========================================================================
    print()
    print("=" * 90)
    print("  ORDERS OF MAGNITUDE GAP ANALYSIS")
    print("=" * 90)

    # How many orders of magnitude separate the quantum signal from
    # relevant neural scales?

    gap_to_synapse = np.log10(s5['V_synapse_mV'] / s5['delta_V_mV']) if s5['delta_V_mV'] > 0 else float('inf')
    gap_to_noise = np.log10(s5['V_noise_mV'] / s5['delta_V_mV']) if s5['delta_V_mV'] > 0 else float('inf')
    gap_to_threshold = np.log10(s5['V_threshold_mV'] / s5['delta_V_mV']) if s5['delta_V_mV'] > 0 else float('inf')

    gap_opt_to_noise = np.log10(0.1 / opt['delta_V_mV']) if opt['delta_V_mV'] > 0 else float('inf')

    print(f"""
  Conservative scenario:
    Gap to synaptic signal (0.5 mV):     {gap_to_synapse:.1f} orders of magnitude
    Gap to thermal noise (0.1 mV):       {gap_to_noise:.1f} orders of magnitude
    Gap to firing threshold (15 mV):     {gap_to_threshold:.1f} orders of magnitude

  Optimistic scenario:
    Gap to thermal noise (0.1 mV):       {gap_opt_to_noise:.1f} orders of magnitude

  What would it take to close the gap?
""")

    # What parameter values would make the signal equal to neural noise?
    target_V_mV = 0.1  # neural noise level
    # delta_V scales linearly with:
    #   - ROS concentration
    #   - encounter radius
    #   - radical formation probability
    #   - conformational energy
    #   - number of MTs
    # So the "closing factor" is target / current
    closing_factor = target_V_mV / s5['delta_V_mV'] if s5['delta_V_mV'] > 0 else float('inf')

    print(f"    To reach neural noise level ({target_V_mV} mV):")
    print(f"    Need {closing_factor:.1e}x increase in aggregate signal.")
    print(f"    This could come from (multiplicatively):")
    print(f"      - ROS {closing_factor**(1/5):.1f}x higher ({s1['c_ROS_nM'] * closing_factor**(1/5):.1f} nM)")
    print(f"      - Or any combination of parameter increases totaling {closing_factor:.1e}x")

    # =========================================================================
    # VERDICT
    # =========================================================================
    print()
    print("=" * 90)
    print("  VERDICT")
    print("=" * 90)

    # Determine the verdict
    if s5['delta_V_mV'] > 0.1:
        verdict = "VIABLE"
        verdict_text = "Level B survives quantitatively"
        explanation = ("The radical pair signal exceeds neural thermal noise "
                      "under conservative parameter estimates.")
    elif opt['delta_V_mV'] > 0.1:
        verdict = "CONDITIONALLY VIABLE"
        verdict_text = "Level B depends critically on parameter values"
        explanation = ("The radical pair signal falls below neural noise under "
                      "conservative estimates but could reach it under "
                      "optimistic (but defensible) parameters.")
    elif opt['delta_V_mV'] > 0.01:
        verdict = "MARGINAL"
        verdict_text = "Level B has a quantitative problem but is not ruled out"
        explanation = ("Even optimistic parameters leave the signal 1-2 orders "
                      "of magnitude below neural noise. Stochastic resonance "
                      "or unknown amplification mechanisms would be needed.")
    else:
        verdict = "NOT VIABLE"
        verdict_text = "Level B has a serious quantitative problem"
        explanation = ("The radical pair signal is many orders of magnitude below "
                      "any relevant neural signal scale, even with optimistic "
                      "parameters. The transduction chain cannot deliver a "
                      "cognitively relevant signal in real time.")

    print(f"""
  VERDICT: {verdict}
  {verdict_text}

  {explanation}

  Key numbers (conservative):
    Radical pair events per neuron per 5 ms:  {s4['events_per_neuron']:.2e}
    Voltage perturbation (pre-amplification): {s5['delta_V_mV']:.2e} mV
    Firing probability bias:                  {s5['firing_prob_bias']:.2e}
    After 51x criticality amplification:      {s5['amplified_bias']:.2e}

  Key numbers (optimistic):
    Voltage perturbation:                     {opt['delta_V_mV']:.2e} mV
    Amplified bias:                           {opt['amplified_bias']:.2e}

  The gap:
    Conservative: {gap_to_noise:.1f} orders of magnitude below neural noise
    Optimistic:   {gap_opt_to_noise:.1f} orders of magnitude below neural noise

  The bottleneck:
    The rate-limiting step is Step 1: radical pair formation rate.
    At 1 nM superoxide with 1% radical formation probability,
    each tubulin dimer sees only ~{s1['effective_rate_per_dimer_s']:.1e} radical pair
    events per second. Even ~13 million dimers per neuron produce
    only ~{s4['events_per_neuron']:.1e} events in a 5 ms neural window.

    The 12.7% yield difference per event is substantial (unlike the
    0.18% excitonic advantage), but the event rate is too low for
    the statistical signal to overcome thermal noise.

  What could save Level B:
    1. ROS bursts during neural activity: [O2^-] can spike to ~100 nM
       during mitochondrial activity bursts (Ref: Murphy 2009).
       This gives 100x more events.
    2. Cooperative/catalytic amplification: if radical pair products
       catalyze further reactions (enzymatic amplification), one event
       could produce many downstream effects.
    3. ROS signaling microdomains: if O2^- is concentrated near MTs
       (e.g., at mitochondria-MT contact sites), local concentration
       could be 100-1000x higher than bulk.
    4. Coherent integration across multiple radical pair lifetimes:
       if the tubulin lattice integrates over longer than 5 ms.
    5. Unknown amplification mechanism between MTs and ion channels.

  What cannot save Level B:
    - More MTs (linear scaling, need 10^{gap_to_noise:.0f}x more)
    - Longer coherence time (already microseconds, which is sufficient)
    - Larger yield difference (12.7% is already large for radical pairs)
    - Criticality amplification alone (51x is not enough by many orders)
""")

    # =========================================================================
    # Summary table
    # =========================================================================
    print("=" * 90)
    print("  SUMMARY TABLE: SIGNAL PROPAGATION THROUGH TRANSDUCTION CHAIN")
    print("=" * 90)

    print(f"""
  {'Step':<45s} {'Signal':<20s} {'Noise scale':<20s} {'SNR':<15s}
  {'-'*100}
  1. RP events per dimer per 5ms               {s1['effective_rate_per_dimer_per_ms']*s3['t_neural_ms']:<20.2e} {'N/A':<20s} {'N/A':<15s}
  2. Yield bias per event                       {s2['delta_E_per_event_kT']:<20.4f} {'1 kT':<20s} {s2['SNR_single_event']:<15.4f}
  3. Signal per MT ({s3['t_neural_ms']} ms)                     {s3['total_signal_kT']:<20.3e} {f'{s3["total_background_noise_kT"]:.1e} kT':<20s} {s3['SNR_MT_vs_background']:<15.3e}
  4. Signal per neuron                          {s4['total_signal_kT']:<20.3e} {f'{s4["total_background_noise_kT"]:.1e} kT':<20s} {s4['SNR_neuron_background']:<15.3e}
  5. Voltage (pre-criticality)                  {f'{s5["delta_V_mV"]:.2e} mV':<20s} {'0.1 mV':<20s} {f'{s5["delta_V_mV"]/0.1:.2e}':<15s}
  6. Firing bias (post-criticality)             {f'{s5["amplified_bias"]:.2e}':<20s} {'~0.01':<20s} {f'{s5["amplified_bias"]/0.01:.2e}':<15s}

  Units: kT = {KT:.3e} J at {T_BODY} K
""")

    print("=" * 90)
    print("  END OF TRANSDUCTION CHAIN ANALYSIS")
    print("=" * 90)

    return {
        'step1': s1, 'step2': s2, 'step3': s3,
        'step4': s4, 'step5': s5, 'step6': s6,
        'sensitivity': sens,
        'verdict': verdict,
        'verdict_text': verdict_text,
        'gap_to_noise_conservative': gap_to_noise,
        'gap_to_noise_optimistic': gap_opt_to_noise,
    }


if __name__ == "__main__":
    main()
