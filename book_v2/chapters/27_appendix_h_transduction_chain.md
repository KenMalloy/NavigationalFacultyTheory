## Appendix H: Microtubule-Anesthesia Complications

The radical pair mechanism produces a 12.7% quantum-classical yield difference per event. The problem is not the size of the signal. The problem is getting enough of it to the right place, fast enough, to matter.

### The Transduction Chain

The calculation follows the quantum signal through six steps, from radical pair formation to neural firing probability. Each step uses conservative parameter estimates.

**Step 1: Radical pair formation rate.** Superoxide diffuses to tryptophan residues on tubulin via Smoluchowski kinetics (D = 1.0 × 10⁻⁹ m²/s, encounter radius 0.5 nm). At 1 nM baseline superoxide, with 8 tryptophan residues per dimer (50% accessible) and 1% radical formation probability per encounter, each dimer experiences roughly 1.5 × 10⁻⁴ events per second.

**Step 2: Signal per event.** Each event contributes a 12.7% yield bias, translating to approximately 0.127 kT of conformational energy difference.

**Steps 3–4: Aggregation.** Across 13,000 dimers per microtubule and 1,000 microtubules per neuron, the signal accumulates to roughly 10 radical pair events per neuron in a 5 ms integration window, producing a voltage shift of approximately 0.0099 mV.

**Step 5: Criticality amplification.** Applying the 51× amplification factor from the branching-network criticality model yields an amplified firing bias of 0.034.

**Step 6: Comparison to noise.** The neural thermal noise floor sits at roughly 0.1 mV. The signal is 0.0099 mV. One order of magnitude below noise.

### The Gap

Under conservative assumptions, the transduction chain falls about 10× short. For comparison, conformational quantum tunneling was suppressed by a factor of 10¹⁵. A 10× gap sits within the range of parameter uncertainty.

### Superoxide Concentration as the Swing Factor

The entire chain scales linearly with superoxide concentration. At 10 nM (upper baseline), the signal reaches the noise floor. At 50–100 nM (plausible during mitochondrial activity bursts), the signal exceeds noise comfortably.

But sustained 10 nM cytosolic superoxide is not easy to maintain. SOD enzymes catalyze superoxide dismutation at near-diffusion-limited rates (k ≈ 1.6 × 10⁹ M⁻¹s⁻¹). The commonly cited steady-state is around 0.1 nM — a hundred times below the threshold where the mechanism works.

### The Duty Cycle Problem

During ordinary cortical processing, local superoxide near microtubules likely stays sub-nanomolar. The fraction of time spent above 10 nM is probably well under 1%. During metabolic stress — mitochondrial "superoxide flashes," receptor-driven enzyme activation — the duty cycle for elevated episodes might reach 1–10% during high-demand periods. The mechanism, if it works at all, is probably episodic rather than continuous.

### When It Becomes Viable

Three factors can independently close the 10× gap:

**ROS elevation.** Activity-dependent superoxide production during cognition could provide 10–100× above baseline at precisely the moments when neural computation is most active.

**Microtubule count.** Large cortical pyramidal neurons may contain up to 77,000 microtubules, yielding roughly one billion tubulin dimers. That alone provides a 77× boost.

**Combined scenario.** Moderate ROS elevation (10 nM) plus higher microtubule count (10,000) puts the signal well above noise without invoking extreme assumptions.

### What Remains Unknown

Five quantities are not well-constrained: the radical formation probability for superoxide-tryptophan encounters in tubulin (we used 1%; it could be 0.1–10%); the conformational coupling efficiency; the local ROS concentration in microtubule-adjacent microdomains; the effective microtubule count in large pyramidal neurons; and the mechanism by which the signal propagates from microtubules to ion channels. Each is experimentally accessible. The transduction chain calculation and underlying simulation code are available in the project repository.

---

