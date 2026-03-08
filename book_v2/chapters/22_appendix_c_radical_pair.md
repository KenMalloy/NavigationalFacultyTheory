## Appendix C: Radical Pair Spin Coherence Calculations

The core question behind Level B is whether a quantum effect can survive long enough, at body temperature, to leave a chemical fingerprint. Excitonic coherence dies in femtoseconds. Radical pair spin coherence operates on a different clock.

We built a minimal radical pair model following Haberkorn (1976) — the same theoretical framework that underlies the avian magnetic compass. The model tracks singlet-triplet interconversion in a radical pair with a single isotropic hyperfine coupling, subject to Zeeman interaction at Earth-strength magnetic field (50 μT) and spin-selective recombination at 310 K. The simulation code is available in the project repository.

### Parameters

The model uses the following values at biological temperature (310 K, kT = 4.28 × 10⁻²¹ J):

- Hyperfine coupling constant: a single isotropic term calibrated to tryptophan-superoxide radical pairs
- Zeeman field: 50 μT (Earth strength)
- Spin relaxation: thermal decoherence appropriate to a warm, wet cellular environment
- Recombination: Haberkorn spin-selective rates for singlet and triplet channels

These are generic radical pair physics parameters, not tubulin-specific chemistry. No particular radical-pair-forming reaction in tubulin has been identified. The model uses a placeholder route — superoxide encountering tryptophan residues — as an order-of-magnitude scenario.

### Results

| Quantity | Value |
|---|---|
| Quantum coherence lifetime | 1.48 μs |
| Classical coherence lifetime | 0.47 μs |
| Quantum singlet yield (Earth field) | 0.797 |
| Classical singlet yield (Earth field) | 0.913 |
| Singlet-yield shift (quantum vs. classical) | 12.69% |
| Quantum-classical trajectory divergence window | 10 μs |
| Yield change, zero field to Earth field | −1.46% |

The quantum and classical trajectories diverge for the full 10 μs simulation window. A 12.7% difference in chemical yield between quantum and classical regimes means the spin dynamics produce a measurably different distribution of reaction products depending on whether coherence is maintained.

### Comparison to Avian Magnetoreception

This effect size sits comfortably alongside the best-characterized radical pair system in biology. Maeda et al. (2012) demonstrated field-dependent yield changes of similar magnitude in synthetic radical pairs designed to mimic cryptochrome. The per-event signal in our model (12.7% yield shift) actually exceeds the roughly 5% yield change reported in avian cryptochrome systems. The difference is that the bird's compass has a known, experimentally validated chemical identity. Ours does not, yet.

### What the Model Does Not Settle

The model operates at the level of generic radical pair physics. It demonstrates that a minimal Haberkorn system produces large, long-lived quantum-classical chemical divergence at 310 K. It does not demonstrate that any such radical pair forms in tubulin at biologically relevant rates.

The placeholder chemical route — superoxide encountering tryptophan residues on tubulin dimers — is plausible but unvalidated. Tubulin has eight tryptophan residues per dimer, and roughly half are estimated to be solvent-accessible. Whether superoxide actually reaches them, and whether the encounter produces a radical pair at meaningful rates, remains an open empirical question. The physics is not the bottleneck. The chemistry is.

---

