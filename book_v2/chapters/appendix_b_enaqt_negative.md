### The Hypothesis

Environment-Assisted Quantum Transport (ENAQT) is a real phenomenon. Mohseni et al. (2008) predicted it theoretically; Panitchayangkoon et al. (2010) confirmed it experimentally in photosynthetic complexes. The idea is that intermediate environmental noise can actually help quantum transport rather than destroying it. Too little noise leaves excitations trapped by quantum interference. Too much noise washes out all quantum effects. At the sweet spot, noise breaks destructive interference without destroying constructive transport pathways.

Microtubules contain vast networks of tryptophan residues with geometry similar to the chromophore networks in photosynthetic complexes. The original Level B hypothesis proposed that consciousness exploits ENAQT in these tryptophan networks to sculpt quantum probabilities. We tested whether the ENAQT advantage survives at physiological temperature in a geometry-informed model of these networks.

It does not.

### The Model

The simulation uses an eight-site linear chain arranged on a helix that approximates the tryptophan network geometry within a microtubule protofilament (radius 2.0 nm, rise 0.8 nm per site, twist 27.7 degrees, dipole tilt 20 degrees). Site energies carry Gaussian static disorder (standard deviation 25 cm^-1). Inter-site couplings follow the dipole-dipole interaction, scaled so that the median nearest-neighbor coupling is 60 cm^-1, consistent with literature estimates for tryptophan networks.

The Hamiltonian captures coherent excitonic hopping between sites. To model the open quantum system, we construct a Liouvillian superoperator in the Quantum Stochastic Walk (QSW) framework of Whitfield et al. (2010). The QSW model adds thermally-weighted Lindblad transition operators between coupled sites, satisfying detailed balance at 310 K. An irreversible sink on the terminal site captures population that successfully transits the chain. Transport efficiency is measured as the total population reaching the sink: eta = 1 - Tr(rho(T)), where rho(T) is the system density matrix at the end of the simulation window.

The environment enters through a Drude-Lorentz spectral density (bath strength 35 cm^-1, cutoff frequency 53 cm^-1). The dephasing rate kappa is derived self-consistently from this spectral density at the median excitonic gap frequency and physiological temperature.

### Three Approaches

We attacked the problem from three angles.

**Phenomenological QSW sweep.** The dephasing rate kappa was swept across six orders of magnitude (gamma/kappa from 10^-3 to 10^3, where gamma represents the coherent coupling scale). At each point, the full Liouvillian was constructed, time-evolved from an initial excitation on site 1, and transport efficiency recorded. This sweep maps the entire landscape from dephasing-dominated to coherent-dominated regimes.

**Bloch-Redfield calculation.** A physically-derived dephasing rate was computed from the Drude-Lorentz spectral density at physiological temperature, yielding kappa_phys = 458 ps^-1 against a median nearest-neighbor coupling V = 11.3 rad/ps. The dimensionless ratio kappa_phys/V = 40.5 places the system deep in the dephasing-dominated regime. The inverse ratio gamma/kappa = 0.025 confirms the system is far from the coherent limit where transport efficiency peaks.

**Evolutionary optimization.** A separate approach used differential evolution to search over geometry parameters (helix dimensions, coupling strengths, disorder levels) for any configuration that produces an ENAQT peak. This search also failed to find configurations where an intermediate-noise optimum exceeds the coherent-limit efficiency at physiological dephasing levels.

### The Numbers

In the verified baseline run (8 sites, default geometry, 310 K), transport efficiency increases monotonically toward the coherent limit. There is no intermediate-noise peak. Maximum efficiency is 0.384 at gamma/kappa = 1000 (essentially the coherent limit). At the physiological operating point (gamma/kappa approximately 0.025), efficiency is approximately 0.327. The quantum advantage over purely classical transport is 0.18%.

The reason is a ratio. Thermal energy at body temperature (kT approximately 40.6 rad/ps at 310 K) is nearly four times the median nearest-neighbor coupling (V = 11.3 rad/ps). The environment overwhelms the coherent dynamics. It is like trying to hear a whisper at a rock concert.

We tested network sizes of 8, 13, 20, and 26 sites. The 0.18% advantage did not scale with network size. There was no hint that larger tryptophan networks would rescue the mechanism.

We also tested conformational tunneling as an alternative excitonic pathway. The quantum tunneling rate was approximately 10^-15 times the classical thermal rate. Not viable by any measure.

### What the Failure Means

The ENAQT sweet spot exists in the microtubule geometry. The problem is that the optimal noise level for quantum transport enhancement is roughly 1,700 times quieter than the actual thermal environment at 310 K. The mechanism requires conditions that do not obtain in living tissue.

### Limitations

This negative result rules out the modeled excitonic transport route under specific assumptions: the QSW dephasing model, a single geometry-informed helix configuration, and fixed sink placement on the terminal site. It does not generalize to all tubulin-derived geometries or all open-quantum-system model classes. Hierarchical equations of motion (HEOM), polaron-transformed master equations, or structural ensembles drawn from crystallographic tubulin data could, in principle, shift the dephasing-to-coupling ratio. No disorder ensemble or Monte Carlo sampling over site energies was performed. The result reflects a single realization of the baseline Hamiltonian.

These caveats are real but narrow. The core physical obstacle, thermal energy roughly four times the coupling strength, is a property of the energy scales involved, not an artifact of the model. Different model classes would need to find a mechanism that circumvents this ratio, not merely adjust it at the margins.

### Code Availability

The transport sweep is implemented in `enaqt_simulation/phase2_transport.py`. The Hamiltonian and Liouvillian builders are in `enaqt_simulation/core.py`. Raw CSV outputs for the dephasing sweep are available in the project repository data supplement. The exact command line for the verified baseline run was:

```
python enaqt_simulation/phase2_transport.py --ratio-count 20 --t-max-ps 20 --dt-ps 0.1
```
