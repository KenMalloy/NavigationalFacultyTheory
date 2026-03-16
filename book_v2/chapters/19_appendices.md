# Appendices

## Appendix A: Simulation Code and Results

### Design Principles

The navigation benchmark tests a single question: can evolution build better navigators when the substrate includes quantum resources than when it does not, given the same optimization budget? Everything in the design exists to keep that question honest.

Four fairness rules govern every run:

1. **Matched training budgets.** Both controllers receive the same number of fitness evaluations. The budget is fixed before either controller is evolved. We did not keep training until the quantum controller won.

2. **Independent optimization.** The classical-adaptive controller is not a crippled version of the quantum controller with quantum features removed. It has its own architecture (a learned state-dependent stochastic gate) and is optimized from scratch via differential evolution under the same budget.

3. **Paired evaluation.** Both controllers face identical mazes with identical random seeds, so maze-level variation affects both sides equally. Per-maze advantage is a paired difference.

4. **The maze is the unit of inference.** Each family includes at least 30 mazes. Trial-level outcomes within a maze are not treated as independent confirmatory samples. Confidence intervals are computed at the maze level using normal-approximation SEM intervals, with win rates using Wilson intervals.

These rules were locked before the confirmatory run. Negative and mixed results are retained, not filtered.

### Maze Generation

Mazes are procedurally generated N-dimensional grids with barrier hyperplanes and random gaps. Three parameters control geometry: side length, number of barriers, and gaps per barrier. Difficulty is classified by detour ratio (shortest path length divided by straight-line distance) into easy, medium, and hard bins. All maze seeds are recorded so every result is reproducible.

For the confirmatory set, 3D mazes used side length 9, 6 barrier hyperplanes, and 2 gaps per barrier, producing an average detour ratio of approximately 1.25x.

### Controller Architectures

The **quantum-adaptive controller** operates a parameterized quantum circuit in a latent space of dimension `latent_dim`. At each time step, radical pair spin dynamics in the latent space produce a singlet yield that depends on the agent's conformational state and the local maze geometry. A state-dependent adaptive measurement basis selects which quantum observable to read. The singlet yield biases movement in the physical maze dimensions. Parameters governing the feedback loop, measurement basis selection, and movement weights are evolved via differential evolution.

The **classical-adaptive controller** replaces the quantum circuit with a learned state-dependent stochastic gate operating in the same observable space. It receives identical sensory inputs and its own independently optimized parameters. This controller is the primary comparator.

Two reality-check baselines are also included: a shortest-path planner with full map knowledge (the classical upper bound) and wall-following heuristics (the lower bound). The planner solves every maze in every family. The benchmark question is therefore: can evolution build better navigators with quantum resources than without them, given the same optimization budget?

### Scaling Sweep

We swept maze dimensionality (2D, 3D, 4D) crossed with latent dimensionality (5D, 6D, 7D), producing three families. Each family includes 30 confirmatory mazes (10 per difficulty bin).

**Family-level results (30 mazes each):**

| Family | Mean normalized advantage | 95% CI | Maze win rate |
|---|---|---|---|
| 2D / 5D | +9.61% | [-0.66%, +19.88%] | 60.0% |
| 3D / 6D | +5.77% | [+2.11%, +9.43%] | 53.3% |
| 4D / 7D | +1.81% | [-3.24%, +6.85%] | 50.0% |

Only the 3D/6D family produces a confidence interval that excludes zero. The 2D/5D family shows a larger point estimate but wider uncertainty that spans zero. The 4D/7D family is a wash.

These results do not support monotonic scaling with latent dimension. The effect is non-monotonic, peaking at an intermediate latent gap of approximately 3 extra dimensions.

### The 90-Maze Confirmatory Result

Pooling all 90 mazes across the three families, the overall normalized advantage is +3.3%, 95% CI [+0.9%, +5.8%]. The confidence interval excludes zero.

### Difficulty Stratification (Exploratory)

Within the 3D/6D family, we examined advantage by difficulty bin. This analysis was not pre-registered; it was conducted after inspecting family-level results and should be treated as hypothesis-generating.

| Difficulty | n mazes | Mean norm. advantage | 95% CI | Win rate |
|---|---|---|---|---|
| Easy | 10 | +5.06% | [-1.30%, +11.42%] | 40% |
| Medium | 10 | +4.39% | [-2.70%, +11.48%] | 50% |
| Hard | 10 | +7.86% | [+1.91%, +13.82%] | 70% |

The hard-maze bin is the only stratum whose CI excludes zero. The gradient is suggestive: harder mazes, where detour ratios force more navigational decisions, produce larger quantum advantage. But with 10 mazes per bin, no strong conclusion is warranted.

### Hard Negatives

The 4D/7D family shows no detectable advantage. Win rates near chance appear even in the positive families. The shortest-path planner solves everything. These are features of honest benchmarking, not embarrassments.

### Code Availability

All simulation code is available in the project repository under `enaqt_simulation/`. Key files: `maze_scaling_sweep.py` (scaling benchmark driver), `maze_navigator.py` (controller and baseline implementations), and `core.py` (quantum dynamics building blocks). The per-maze CSV for the confirmatory run is in `enaqt_simulation/results/`. Every command line used for the cited runs is recorded in the CSV's `command_line` column.

---

## Appendix B: ENAQT Simulation — The Negative Result

### The Hypothesis

Environment-Assisted Quantum Transport (ENAQT) is a real phenomenon. Mohseni et al. (2008) predicted it theoretically; Panitchayangkoon et al. (2010) confirmed it experimentally in photosynthetic complexes. The idea is that intermediate environmental noise can actually help quantum transport rather than destroying it. Too little noise leaves excitations trapped by quantum interference. Too much noise washes out all quantum effects. At the sweet spot, noise breaks destructive interference without destroying constructive transport pathways.

Microtubules contain vast networks of tryptophan residues with geometry similar to the chromophore networks in photosynthetic complexes. The original Level B hypothesis proposed that consciousness exploits ENAQT in these tryptophan networks to sculpt quantum probabilities. We tested whether the ENAQT advantage survives at physiological temperature in a geometry-informed model of these networks.

It does not.

### The Model

The simulation uses an eight-site linear chain arranged on a helix that approximates the tryptophan network geometry within a microtubule protofilament (radius 2.0 nm, rise 0.8 nm per site, twist 27.7 degrees, dipole tilt 20 degrees). Site energies carry Gaussian static disorder (standard deviation 25 cm⁻¹). Inter-site couplings follow the dipole-dipole interaction, scaled so that the median nearest-neighbor coupling is 60 cm⁻¹, consistent with literature estimates for tryptophan networks.

The Hamiltonian captures coherent excitonic hopping between sites. To model the open quantum system, we construct a Liouvillian superoperator in the Quantum Stochastic Walk (QSW) framework of Whitfield et al. (2010). The QSW model adds thermally-weighted Lindblad transition operators between coupled sites, satisfying detailed balance at 310 K. An irreversible sink on the terminal site captures population that successfully transits the chain. Transport efficiency is measured as the total population reaching the sink: η = 1 − Tr(ρ(T)), where ρ(T) is the system density matrix at the end of the simulation window.

The environment enters through a Drude-Lorentz spectral density (bath strength 35 cm⁻¹, cutoff frequency 53 cm⁻¹). The dephasing rate κ is derived self-consistently from this spectral density at the median excitonic gap frequency and physiological temperature.

### Three Approaches

We attacked the problem from three angles.

**Phenomenological QSW sweep.** The dephasing rate κ was swept across six orders of magnitude (γ/κ from 10⁻³ to 10³). At each point, the full Liouvillian was constructed, time-evolved from an initial excitation on site 1, and transport efficiency recorded. This sweep maps the entire landscape from dephasing-dominated to coherent-dominated regimes.

**Bloch-Redfield calculation.** A physically-derived dephasing rate was computed from the Drude-Lorentz spectral density at physiological temperature, yielding κ_phys = 458 ps⁻¹ against a median nearest-neighbor coupling V = 11.3 rad/ps. The dimensionless ratio κ_phys/V = 40.5 places the system deep in the dephasing-dominated regime.

**Evolutionary optimization.** A separate approach used differential evolution to search over geometry parameters (helix dimensions, coupling strengths, disorder levels) for any configuration that produces an ENAQT peak. This search also failed to find configurations where an intermediate-noise optimum exceeds the coherent-limit efficiency at physiological dephasing levels.

### The Numbers

In the verified baseline run (8 sites, default geometry, 310 K), transport efficiency increases monotonically toward the coherent limit. There is no intermediate-noise peak. Maximum efficiency is 0.384 at γ/κ = 1000. At the physiological operating point (γ/κ ≈ 0.025), efficiency is approximately 0.327. The quantum advantage over purely classical transport is 0.18%.

The reason is a ratio. Thermal energy at body temperature (kT ≈ 40.6 rad/ps at 310 K) is nearly four times the median nearest-neighbor coupling (V = 11.3 rad/ps). The environment overwhelms the coherent dynamics.

We tested network sizes of 8, 13, 20, and 26 sites. The 0.18% advantage did not scale with network size. We also tested conformational tunneling as an alternative excitonic pathway. The quantum tunneling rate was approximately 10⁻¹⁵ times the classical thermal rate. Not viable.

### Limitations

This negative result rules out the modeled excitonic transport route under specific assumptions: the QSW dephasing model, a single geometry-informed helix configuration, and fixed sink placement on the terminal site. It does not generalize to all tubulin-derived geometries or all open-quantum-system model classes. The core physical obstacle — thermal energy roughly four times the coupling strength — is a property of the energy scales involved, not an artifact of the model. Different model classes would need to find a mechanism that circumvents this ratio, not merely adjust it at the margins.

### Code Availability

The transport sweep is implemented in `enaqt_simulation/phase2_transport.py`. The Hamiltonian and Liouvillian builders are in `enaqt_simulation/core.py`. Raw CSV outputs for the dephasing sweep are available in the project repository.

---

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

## Appendix D: TDA Reanalysis — Methods and Results

NFT makes a specific temporal ordering prediction: topological complexity of neural dynamics should decline before classical activity metrics during anesthetic induction. We tested this prediction against a public propofol dataset. The topology did not lead.

### Dataset

We used OpenNeuro DS005620, a propofol sedation study with 21 subjects. Each subject has resting-state EEG recordings in awake, sedated, and deeply sedated conditions. The dataset is BIDS-compliant and publicly available.

A critical limitation: DS005620 does not expose true propofol induction timing within the rest recordings. We use the acquisition order of the recording runs as a proxy for the induction trajectory. Every result that follows should be read with this constraint in mind.

### Pipeline

The analysis pipeline consists of four stages, all available in the project repository:

1. **Download** (01_download.py): Fetches raw data from OpenNeuro.
2. **Preprocessing** (02_preprocess.py): Band-pass filtering, downsampling, ICA-based artifact rejection, and epoching.
3. **Feature computation** (03_compute_metrics.py): Computes both classical and topological features per epoch.
4. **Temporal ordering test** (04_temporal_ordering.py): Does topology decline first?

### Features Computed

**Classical comparators.** Two established consciousness-sensitive metrics: Lempel-Ziv complexity (following Schartner et al. 2015) and alpha-band weighted phase lag index (wPLI, following Vinck et al. 2011).

**Topological features.** Persistent homology of channel-correlation matrices using a Vietoris-Rips filtration, yielding Betti numbers, persistence entropy, total persistence per homological dimension, and a composite topological complexity score.

### Results

| Comparator | n | Median lag (epochs) | p-value | Topology-first proportion |
|---|---|---|---|---|
| Lempel-Ziv | 17 | −57.0 | 0.958 | 0.12 |
| Alpha wPLI | 18 | −59.5 | 0.998 | 0.11 |

Against both comparators, classical metrics declined first by a wide margin. Only 11–12% of subjects showed topology-first ordering — consistent with chance. The prediction is not supported.

The result is directional. Topological features did not just fail to lead — they consistently lagged behind classical markers. A future dataset with marked induction onsets within continuous recordings could confirm or reverse this finding.

---

## Appendix E: Non-Neural Evidence

Chapter 6 raised a consequence of the FtsZ-to-tubulin story that deserves closer examination: if consciousness scales with microtubule network complexity, then navigational capacity should appear, in graded form, across the eukaryotic tree of life. This appendix surveys the evidence. It is suggestive but not conclusive, and I want to be clear about the difference.

### Slime Molds

*Physarum polycephalum* is a single-celled organism with no neurons, no synapses, and no nervous system. It solves mazes. Nakagaki and colleagues (2000) placed *Physarum* in a maze with food at two exits and showed that the organism's protoplasmic tube network reorganized to connect both food sources along the shortest path. Tero and colleagues (2010) scaled this up: when food sources were arranged to mimic the positions of Tokyo rail stations, *Physarum* produced transport networks comparable in efficiency to the actual Tokyo rail system.

The anticipation result is harder to dismiss as reflexive chemistry. Saigusa and colleagues (2008) exposed *Physarum* to periodic environmental changes and then stopped the changes. The organism continued to slow its movement at the intervals where the stress had previously occurred. It was anticipating a pattern that no longer existed. Boisseau, Vogel, and Dussutour (2016) demonstrated habituation — a form of learning previously thought to require neurons. Critically, *Physarum*'s memory traces were overwritable in light of new information, meeting accepted criteria for genuine adaptive memory rather than passive chemical traces.

All of this is mediated by cytoskeletal networks. *Physarum* has no wires. It has microtubules and actin.

### Fungi

Mycelial networks present a different test case. Cord-forming wood-decay fungi have no central anything, yet they exhibit network-level plasticity across timescales of months. Fukasawa, Savoury, and Boddy (2020) showed that when a mycelium discovered a food source and was then placed in a fresh environment, it emerged from the same side of the starting block that had previously led to reward — spatial memory without a single neuron. Money (2021) has argued explicitly for hyphal and mycelial consciousness, though that claim outpaces what the evidence can support. What the evidence does support is history-dependent, adaptive network behavior in an organism whose computational substrate is its cytoskeleton.

### Plants

Plant cells are among the most microtubule-rich eukaryotic cells. Their cortical microtubule arrays reorganize dynamically in response to environmental stimuli — light, gravity, mechanical stress. The "plant neurobiology" movement, documented by Calvo and colleagues (2017), has identified electrical signaling, adaptive behavior, and forms of learning in organisms with no neural tissue. The movement remains controversial, and some of the stronger claims have been challenged on methodological grounds. The microtubule density, however, is not in dispute.

### The Comparative Cognition Challenge

If microtubule network complexity were the only variable that mattered, navigational capacity should scale with it across species. The prediction runs into trouble immediately. Cephalopods achieve remarkable behavioral flexibility through a radically different neural architecture than vertebrates. Insects navigate complex environments through architectures orders of magnitude smaller than vertebrate brains. Multiple architectural solutions can produce flexible behavior, and microtubule complexity may predict navigational capacity within clades but not across them. This is an honest limitation.

### The Cambrian Timing

Complex microtubule networks appear in animals around the Cambrian explosion, 540 million years ago, coinciding with the first major radiation of behaviorally complex animals. The coincidence is suggestive. It is also untestable — we have no preserved cytoskeletons from Cambrian organisms.

### Assessment

The evidence is consistent with NFT's "dial not switch" prediction. It does not confirm it. The strongest reading is that the eukaryotic tree of life contains graded navigational capacity that correlates with cytoskeletal complexity. The weakest reading is that cytoskeletal networks are versatile computational substrates for reasons that have nothing to do with quantum coupling. Both readings accommodate the data. The experiments that could distinguish them — measuring quantum coherence properties in *Physarum*'s cytoskeletal networks, for instance — have not been done.

---

## Appendix F: Entropy Taxonomy

The word "entropy" appears throughout this book doing at least seven different jobs. This appendix specifies which notion is doing what work, so that each usage can be evaluated on its own terms.

### Signal Entropy (Shannon/Lempel-Ziv)

Shannon entropy — H(X) = −Σ p(x) log p(x) — measures unpredictability of a probability distribution. When applied to neural time series, typically via Lempel-Ziv complexity or sample entropy of EEG/fMRI recordings, it quantifies the complexity of the brain's current output. This is what most consciousness researchers mean when they say "entropy." The empirical result is robust and replicated: signal entropy drops during anesthesia, rises during wakefulness, and distinguishes minimally conscious patients from unresponsive ones.

### Trajectory Entropy

The novel concept in this book. Trajectory entropy measures uncertainty over distributions of future states, conditioned on an organism's goals and available actions. The critical distinction: signal entropy describes what the brain is doing now. Trajectory entropy describes what consciousness reduces — the space of what could happen next, narrowed by navigational selection. The two are correlated (suppressing consciousness reduces both), but they are not the same quantity. A classical Bayesian agent can reduce trajectory entropy through prediction and planning. NFT's Level B claim is that conscious systems do this more efficiently than classical processes under matched biological constraints.

### Tsallis Entropy

A one-parameter generalization of Shannon entropy: S_q = (1/(q−1))(1 − Σ p(x)^q). When q = 1, it reduces to Shannon. When q > 1, it is sensitive to heavy-tailed distributions and long-range correlations — the statistical signatures of systems at criticality. The Tsallis q-parameter appears in Chapter 16 as a diagnostic marker: biological neural systems at criticality yield q > 1; classical digital systems yield q ≈ 1.

### Rényi Entropy

Another one-parameter generalization: H_α = (1/(1−α)) log(Σ p(x)^α). Like Tsallis, it reduces to Shannon as α → 1 and is sensitive to distributional tails. The relationship between Tsallis and Rényi is monotonic — they carry the same ordinal information for matched parameters — but their additivity properties differ. Rényi is additive for independent subsystems; Tsallis is not.

### Perturbational Complexity Index (PCI)

An entropy-derived consciousness measure developed by Casali and colleagues (2013). PCI combines TMS stimulation with algorithmic complexity of the evoked EEG response. It measures how complex the brain's *response to perturbation* is. A system at criticality should show maximal PCI; departures from criticality should reduce it. PCI reliably tracks consciousness level across wakefulness, sleep, anesthesia, and disorders of consciousness without requiring behavioral report.

### Conditional Entropy (Including Negative Quantum Conditional Entropy)

Classical conditional entropy, H(A|B) = H(A,B) − H(B), measures uncertainty remaining about system A after observing system B. It is always non-negative classically: knowing more never makes you more uncertain. Quantum conditional entropy breaks this rule. For entangled states, it can go negative — something classically forbidden. Negative conditional entropy is a genuine quantum-only resource, provably inaccessible to classical systems. The book invokes it as a theoretical ceiling that conscious systems, if quantum-coupled, might approach.

### Thermodynamic Entropy

The entropy of the second law. It defines the arrow of time and the gradient along which NFT claims consciousness navigates. When the book says "the entropy gradient" or "the entropic current," this is the notion in play. Consciousness, on NFT's account, does not reverse the current. It steers within it.

### How They Fit Together

The argument moves across these notions deliberately. Thermodynamic entropy provides the navigational gradient. Shannon, Tsallis, and Rényi provide the empirical measurement tools. PCI provides the clinical bridge. Trajectory entropy is what consciousness actually reduces. Negative conditional entropy marks the boundary between what classical and quantum systems can achieve.

---

## Appendix G: Extended Engagement with Competing Frameworks

Any theory of consciousness owes a debt to its competitors. If you can't articulate what rival frameworks get right, you haven't understood the problem well enough to propose a solution.

**The three-level evidential framework.** The main text organizes NFT's empirical commitments into three levels: substrate tests (does the proposed quantum effect exist in the relevant biology?), linkage tests (does perturbing that effect change conscious access?), and discriminative tests (is the observed pattern better explained by the quantum-linked model than by a classical alternative?). A substrate result without linkage is physics, not consciousness science. A linkage result without a discriminative comparison is a correlation, not a mechanism.

**Quantum cognition models.** Busemeyer and Pothos have developed a sophisticated program showing that quantum probability theory describes human decision-making patterns better than classical probability in several well-studied paradigms: conjunction fallacy violations, order effects in survey responses, the disjunction effect. Their work is careful, replicable, and does not require a quantum brain. The math is quantum. The substrate need not be.

NFT agrees with the math. The disagreement is about whether the fit is a coincidence. Quantum cognition treats quantum probability as a useful formalism. NFT proposes that the formalism fits because the underlying substrate is, in fact, quantum. If NFT is right, the fit should track cases where the proposed biological substrate is most active. That is a testable difference.

**Recurrent Processing Theory.** Lamme's RPT holds that consciousness arises from recurrent neural processing. RPT has genuine empirical traction: recurrent processing correlates with reportable awareness in visual masking paradigms, and disrupting it disrupts conscious access. NFT subsumes RPT. Recurrent processing is the neural architecture through which navigational selection operates. RPT answers a "where in the brain" question. NFT answers a "why does recurrent processing produce experience and feedforward processing doesn't?" question.

**GNWT after COGITATE.** The COGITATE adversarial collaboration, published in *Nature* in 2025, substantially challenged key predictions of both GNWT and IIT. Neither theory was killed. Both were wounded in specific, documented ways. NFT reads this result as evidence that workspace broadcast and information integration are subsystems of something larger, not competitors for the whole explanation.

**Hard criteria for any quantum consciousness theory.** Any serious quantum consciousness proposal must: identify a specific quantum effect in the relevant biological substrate; show that perturbing it changes something about consciousness, not just neural activity; demonstrate that the observed pattern cannot be equally well explained without the quantum mechanism. NFT currently clears the first criterion partially, the second not at all, and the third in simulation only. A framework that honestly reports where its evidence ends is more trustworthy than one that pretends the evidence is complete.

**Integrated World Modeling Theory.** Safron's IWMT (2020; 2022) is the closest rival unification. It combines IIT, GNWT, the Free Energy Principle, and active inference under variational free energy minimization. Its mathematical formalism is more developed than NFT's. It expresses consciousness in the language of Bayesian inference, the brain as a prediction machine that builds internal models, weights them by confidence, and passes corrections up and down a hierarchy. NFT's formalism (Chapter 17) has not yet reached that depth.

NFT pushes further on two problems IWMT's elegance leaves open. Modern LLMs arguably satisfy IWMT's formal criteria — they perform variational inference, construct world models, minimize prediction error — and IWMT has not specified a precise embodiment threshold that excludes them. NFT's four conditions do. Second, IWMT describes processes that unfold *in* time but does not account *for* time. NFT's grounding in the entropy gradient and the block universe at least attempts an answer.

IWMT describes the computational engine of the vehicle. NFT describes what driving is and how the engine connects to the road. A future synthesis would be stronger than either alone.

---

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

## Appendix I: Philosophical Supplements

**The block universe in more detail.** The block universe sits at the intersection of two ideas that most physicists accept individually and find disturbing together. First: Einstein's field equations are time-symmetric. The laws of physics contain no variable for "now." Second: the relativity of simultaneity means that two events simultaneous for one observer are sequential for another. Putnam's argument follows: if my future is already your present, and your present is real, then my future is real too.

The tension with quantum mechanics is real and unresolved. Quantum measurement appears to introduce genuine indeterminacy, moments where the future is not yet fixed. The growing block alternative, developed by Broad and refined by Tooley, offers a middle path: the past and present are real, the future is not yet. NFT's Level C is more naturally compatible with the growing block than with strict eternalism, because navigational selection requires that the alternatives are genuinely available. But the growing block requires a privileged present, and special relativity provides no natural candidate for that boundary. NFT does not require settling this debate. Level C offers an engagement with the question, not a solution.

**Mary's room and the knowledge argument.** Frank Jackson's thought experiment: Mary has learned everything physical there is to know about color vision, but she has lived in a black-and-white room. When she sees red for the first time, does she learn something new?

NFT's response is specific. Mary's physical knowledge was third-person, observational, descriptive. What she gains when she sees red is the first-person disturbance that accompanies a measurement-like update of her own perceptual state. The back-action proposal from Chapter 12 suggests that qualitative character is tied to the physical disturbance intrinsic to a measurement-like process. Mary knew everything about color processing from the outside. She had never undergone the specific disturbance that constitutes seeing red from the inside. On the dissolution claim of Chapter 12, Mary's gap is between observing a process and undergoing it. She knew everything about color processing from the outside. She had never been the apparatus that is changed by seeing red. These are not two kinds of thing. They are one thing with two sides [C].

**Causal closure and quantum indeterminacy.** Quantum indeterminacy does not provide a clean loophole for mental causation. It looks like it might: if physical law determines the probabilities but not the outcomes, there is causal slack. But filling indeterminacy with consciousness converts probabilistic physical law into deterministic psychophysical law, and now you need to explain why quantum statistics look random when they are being steered. NFT's approach is not to claim that consciousness supplements physical law. It is to claim that the measurement-like process through which definite outcomes emerge is itself the locus of conscious experience. Consciousness does not push the dice. Consciousness is the rolling.

**The edge cases.** Any theory of consciousness has to answer the photodiode question: a photodiode performs measurement and experiences back-action, so is it conscious? NFT's answer is the loop. A photodiode resets after each photon. Its next measurement is identical to its last. The world changes it, but it asks the same question every time. A thermostat is closer: the outcome changes what happens next, but the measurement basis is fixed at the factory. It asks the same question forever. Neither system uses measurement outcomes to reshape the next measurement. Neither has the adaptive feedback loop that the back-action thesis requires. The traditional philosophical zombie (a system functionally identical to a conscious being but lacking experience) maps onto NFT's back-action evasion prediction (Chapter 12): eliminate the quantum back-action while preserving classical signaling, and you get functional behavior without the loop. Whether that system would lack experience is the empirical question the prediction is designed to test [B].

**The Gödel analogy and its limits.** The constraint hypothesis draws an analogy to Gödel's incompleteness theorems: a sufficiently complex formal system cannot prove all truths about itself from within. The analogy is precise in one respect: both involve self-reference generating principled limits on internal representation. Where it breaks down: Gödel's theorems apply to formal axiomatic systems with specific properties. Brains are not formal systems. They are not consistent. They do not operate by syntactic proof. The constraint hypothesis uses Gödel as a structural metaphor, not a theorem. The claim is that self-modeling limits are a feature of the territory, not a defect of current theory. But metaphors, however useful, are not proofs.

---

## Appendix J: Quantum Interpretations

NFT's empirical commitments are at Levels A and B. Level C touches quantum interpretation, and different interpretations receive the theory differently.

**Copenhagen.** NFT fits naturally. The proposal is that biological measurement-like processes — radical pair chemistry in microtubules — constitute a physical instantiation of measurement. Consciousness is not an external observer collapsing wavefunctions from outside physics. It is the measurement process itself, instantiated in biological hardware. Copenhagen does not specify what counts as a measurement apparatus. NFT offers a candidate answer.

**Many-worlds.** At Level A, this is fine. Navigation through possibility space maps onto the branching structure. At Level B, the tension sharpens. NFT proposes that consciousness sculpts probabilities. In many-worlds, all outcomes are realized. There is nothing to sculpt. The mechanism needs somewhere to operate. Many-worlds makes the mechanism either redundant or incoherent. NFT at Level B sits uncomfortably here.

**Bohmian mechanics.** Compatible but awkward. The hidden variables provide determinism that Level B does not need. If radical pair outcomes are already determined, consciousness is following a script it cannot read. The navigational language survives as a description. The agency drops out.

**QBism.** The most natural home. Consciousness is the agent assigning probabilities. Possibility space is the agent's structured landscape of expectations. The Born rule is a normative constraint on rational updating. QBism gives NFT the agent but not the territory — if you want possibility space to be physically real, as Level C proposes, QBism will not take you there.

**Objective collapse (GRW/CSL).** Partially compatible. If collapse parameters could depend on a consciousness-relevant variable, objective collapse provides a mechanism for consciousness-weighted actualization. But the parameter space is tightly constrained by modern experimental bounds. The surviving parameter corners are narrow.

**The early universe problem.** Every consciousness-linked interpretation must answer: what collapsed the wavefunction before conscious observers existed? NFT does not have a novel answer. It inherits whichever answer its chosen interpretation provides. This is not a unique weakness — every interpretation-dependent claim faces it — but it is a real one.

---

## Appendix K: Comparison with Stapp

Henry Stapp's quantum mind theory is the nearest ancestor to NFT's Level B, and the comparison deserves care. Stapp gets several things right. He also gets several things wrong in ways that are instructive.

**Shared commitments.** Both theories hold that quantum indeterminacy is the physical basis for genuine alternatives. Both hold that consciousness is connected to the measurement process. Both reject epiphenomenalism. Both take the quantum Zeno effect seriously. These are not small agreements.

**Key difference: scale.** Stapp locates the relevant quantum process at the macroscopic neural scale, invoking von Neumann's Process 1 as an act of conscious attention operating on brain-state superpositions. NFT locates the process at the molecular scale. Radical pair chemistry in microtubule-associated proteins provides the quantum substrate. The superpositions are molecular, not neural.

This matters for the decoherence problem. Tegmark's calculation shows that macroscopic neural superpositions decohere in roughly 10⁻¹³ to 10⁻²⁰ seconds. Stapp's theory must either refute Tegmark or accept that the relevant superpositions are not neural-scale. NFT sidesteps this: molecular radical pair states have coherence times on the order of microseconds and are continuously regenerated.

**Key difference: mechanism of volition.** Stapp uses the quantum Zeno effect as his primary mechanism for conscious will: rapid observation holds a neural state in place. NFT uses both Zeno and anti-Zeno effects. Zeno stabilizes perceptual states. Anti-Zeno accelerates transitions. The ratio between them depends on the spectral density of the environment and the measurement rate, giving the theory a tunable parameter rather than a single mechanism. Attention is not just freezing. It is also releasing.

**Key difference: biological substrate.** Stapp's theory has no identified biological mechanism. Process 1 is described in the language of quantum measurement theory, not biochemistry. NFT proposes microtubule radical pairs — specific enough to be wrong. The spin coherence times, the chemical kinetics, the downstream coupling to protein conformation, all of these are individually measurable.

**Assessment.** Stapp opened a door that most scientists preferred to keep closed: the possibility that quantum measurement and consciousness are physically connected. That was an act of intellectual courage. The limitation is that he never walked through the door far enough to find the biology. NFT attempts to walk further. Whether the biology it finds is the right biology remains an open experimental question.

---

## Appendix L: The Diagnostic Panel

Five quantitative markers translate the four conditions of Chapter 16 into measurable predictions. Each marker asks a specific question and yields a specific answer depending on the system you point it at.

| Marker | Question | Measure | Biological prediction | LLM prediction |
|---|---|---|---|---|
| 1. Entropy regime | Critical or ordinary statistics? | Tsallis q-parameter | q > 1 | q ≈ 1 |
| 2. Topological complexity | High-dimensional connection structures? | Betti numbers, persistence diagrams | Persistent high-dimensional features | Absent |
| 3. Quantum probability signatures | Quantum or classical decision rules? | Busemeyer QQ equality | Satisfied | Violated |
| 4. Time-irreversibility | Physics different forward vs. backward? | Entropy production rate | State-dependent irreversibility | Time-symmetric |
| 5. Trajectory entropy reduction | Better-than-classical uncertainty reduction? | Trajectory entropy vs. decision depth | Scaling advantage | No advantage |

The five markers are jointly overdetermined. A system that fails all five in the predicted pattern provides strong evidence that behavioral emulation does not imply identity of physical mechanism.

The critical test is Level 2 (classical neuromorphic at criticality) versus Level 3 (quantum neuromorphic at criticality). NFT predicts that Level 2 systems will satisfy Markers 1, 2, and 4 but fail Markers 3 and 5 specifically, because those markers depend on genuine quantum indeterminacy rather than network architecture alone. If Level 2 and Level 3 are indistinguishable across all five markers, NFT's quantum commitment is falsified.

---

# References

### Tier 1: Peer-Reviewed Empirical and Computational Studies

Aharonov, Y., Albert, D. Z., & Vaidman, L. (1988). How the result of a measurement of a component of the spin of a spin-1/2 particle can turn out to be 100. *Physical Review Letters, 60*(14), 1351–1354.

Benzi, R., Sutera, A., & Vulpiani, A. (1982). Stochastic resonance in climatic change. *Tellus, 34*(1), 10–16.

Blackburne, G., et al. (2025). Complex slow waves in the human brain under 5-MeO-DMT. *Cell Reports, 44*(8), 116040.

Boisseau, R. P., Vogel, D., & Dussutour, A. (2016). Habituation in non-neural organisms: evidence from slime moulds. *Proceedings of the Royal Society B: Biological Sciences, 283*(1829), 20160446.

Casali, A. G., et al. (2013). A theoretically based index of consciousness independent of sensory processing and behavior. *Science Translational Medicine, 5*(198), 198ra105.

Cogitate Consortium. (2025). Adversarial testing of global neuronal workspace and integrated information theories of consciousness. *Nature, 642*(8066), 133–142.

Cripe, J., et al. (2019). Measurement of quantum back action in the audio band at room temperature. *Nature, 568*, 364–367.

Fukasawa, Y., Savoury, M., & Boddy, L. (2020). Ecological memory and relocation decisions in fungal mycelial networks: responses to quantity and location of new resources. *ISME Journal, 14*(2), 380–388.

Irrmischer, M., et al. (2025). DMT-induced shifts in criticality correlate with self-dissolution. *Journal of Neuroscience, 46*(2), e0344252025.

Itano, W. M., et al. (1990). Quantum Zeno effect. *Physical Review A, 41*(5), 2295–2300.

Li, N., et al. (2018). Nuclear spin attenuates the anesthetic potency of xenon isotopes in mice. *Anesthesiology, 129*(2), 271–277.

Li, N., et al. (2025). Microtubule-modulating drugs alter sensitivity to isoflurane in mice. *BMC Anesthesiology, 25*, 109.

Lori, N., & Machado, J. (2026). Gridography tractography reveals communication between key areas from global workspace and integrated information theories of consciousness. *Scientific Reports, 16*, 1617.

Maeda, K., et al. (2012). Magnetically sensitive light-induced reactions in cryptochrome are consistent with its proposed role as a magnetoreceptor. *Proceedings of the National Academy of Sciences, 109*(13), 4774–4779.

Mohseni, M., Rebentrost, P., Lloyd, S., & Aspuru-Guzik, A. (2008). Environment-assisted quantum walks in photosynthetic energy transfer. *Journal of Chemical Physics, 129*(17), 174106.

Nakagaki, T., Yamada, H., & Tóth, Á. (2000). Maze-solving by an amoeboid organism. *Nature, 407*, 470.

OpenNeuro. (2024). *A repeated awakening study exploring the capacity of complexity measures to capture dreaming during propofol sedation* (Version 1.0.0) [Data set]. OpenNeuro. DOI: 10.18112/openneuro.ds005620.v1.0.0.

Ort, A., et al. (2023). TMS-EEG and resting-state EEG applied to altered states of consciousness: oscillations, complexity, and phenomenology. *iScience, 26*(5), 106589.

Pallavicini, C., et al. (2023). Neural and subjective effects of inhaled N,N-dimethyltryptamine in natural settings. *Journal of Psychopharmacology, 37*(7), 689–702.

Panitchayangkoon, G., Hayes, D., Fransted, K. A., et al. (2010). Long-lived quantum coherence in photosynthetic complexes at physiological temperature. *Proceedings of the National Academy of Sciences, 107*(29), 12766–12770.

Piccinini, J. I., et al. (2025). Transient destabilization of whole brain dynamics induced by N,N-dimethyltryptamine (DMT). *Communications Biology, 8*(1), 409.

Saigusa, T., et al. (2008). Amoebae anticipate periodic events. *Physical Review Letters, 100*, 018101.

Santiago-Alarcon, D., et al. (2020). Quantum aspects of evolution: a contribution towards evolutionary explorations of genotype networks via quantum walks. *Journal of the Royal Society Interface, 17*(172), 20200567.

Santoro, A., et al. (2024). Higher-order connectomics of human brain function reveals local topological signatures. *Nature Communications, 15*, 10244.

Schartner, M., et al. (2015). Complexity of multi-dimensional spontaneous EEG decreases during propofol induced general anaesthesia. *PLOS ONE, 10*(8), e0133532.

Tero, A., et al. (2010). Rules for biologically inspired adaptive network design. *Science, 327*(5964), 439–442.

Timmermann, C., et al. (2023). Human brain effects of DMT assessed via EEG-fMRI. *PNAS, 120*(13), e2218949120.

Turin, L., et al. (2014). Electron spin changes during general anesthesia in *Drosophila*. *PNAS, 111*(34), E3524–E3533.

VanRullen, R. (2016). Perceptual cycles. *Trends in Cognitive Sciences, 20*(10), 723–735.

Vinck, M., Oostenveld, R., van Wingerden, M., et al. (2011). An improved index of phase-synchronization for electrophysiological data in the presence of volume-conduction, noise and sample-size bias. *NeuroImage, 55*(4), 1548–1565.

Zadeh-Haghighi, H., et al. (2026). Tubulin polymerization dynamics are influenced by magnetic isotope effects consistent with the radical pair mechanism. *Science Advances, 12*(7), eady8317.

### Tier 2: Peer-Reviewed Theoretical, Review, and Foundational Works

Baars, B. J. (1988). *A Cognitive Theory of Consciousness.* Cambridge University Press.

Busemeyer, J. R., & Bruza, P. (2012). *Quantum Models of Cognition and Decision.* Cambridge University Press.

Callender, C. (2017). *What Makes Time Special?* Oxford University Press.

Calvo, P., Sahi, V. P., & Trewavas, A. (2017). Are plants sentient? *Plant, Cell & Environment, 40*(11), 2858–2869.

Carhart-Harris, R. L., et al. (2014). The entropic brain: A theory of conscious states informed by neuroimaging research with psychedelic drugs. *Frontiers in Human Neuroscience, 8*, 20.

Carhart-Harris, R. L. (2018). The entropic brain — revisited. *Neuropharmacology, 142*, 167–178.

Chalmers, D. (1995). Facing up to the problem of consciousness. *Journal of Consciousness Studies, 2*(3), 200–219.

Dehaene, S., & Changeux, J.-P. (2011). Experimental and theoretical approaches to conscious processing. *Neuron, 70*(2), 200–227.

DeLancey, C. (2023). *Consciousness as Complex Event.* Routledge.

Edwards, D. J. (2025). Further N-Frame networking dynamics of conscious observer-self agents via a functional contextual interface: predictive coding, double-slit quantum mechanical experiment, and decision-making fallacy modeling as applied to the measurement problem in humans and AI. *Frontiers in Computational Neuroscience, 19*, 1551960.

Fahrenfort, J. J., et al. (2025). Criterion placement confounds in adversarial collaborations on consciousness. *Neuroscience of Consciousness, 2025*(1), niae048.

Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience, 11*, 127–138.

Gödel, K. (1931). Über formal unentscheidbare Sätze der Principia Mathematica und verwandter Systeme I. *Monatshefte für Mathematik und Physik, 38*, 173–198.

Grüning, C., & Bhatt, D. (2016). Dark state population determines magnetic sensitivity in radical pair magnetoreception model. *Scientific Reports, 6*, 22417.

Hiscock, H. G., et al. (2024). Quantum Zeno recovery of tightly bound radical pair magnetosensitivity. *Nature Communications, 15*, 2045.

Haberkorn, R. (1976). Density matrix description of spin-selective radical pair reactions. *Molecular Physics, 32*(5), 1491–1493.

Hameroff, S., & Penrose, R. (2014). Consciousness in the universe: A review of the 'Orch OR' theory. *Physics of Life Reviews, 11*(1), 39–78.

Hemmo, M., & Shenker, O. (2022). The second law of thermodynamics and the psychological arrow of time. *British Journal for the Philosophy of Science, 73*(1), 85–107.

Hoffman, D. D. (2019). *The Case Against Reality.* W. W. Norton.

Kleiner, J., & Hoel, E. (2021). Falsification and consciousness. *Neuroscience of Consciousness, 2021*(1), niab001.

Kofman, A. G., & Kurizki, G. (2000). Acceleration of quantum decay processes by frequent observations. *Nature, 405*, 546–550.

Massimini, M., et al. (2005). Breakdown of cortical effective connectivity during sleep. *Science, 309*(5744), 2228–2232.

Minkowski, H. (1908). Raum und Zeit. *Physikalische Zeitschrift, 10*, 75–88.

Misra, B., & Sudarshan, E. C. G. (1977). The Zeno's paradox in quantum theory. *Journal of Mathematical Physics, 18*(4), 756–763.

Money, N. P. (2021). Hyphal and mycelial consciousness: the concept of the fungal mind. *Fungal Biology, 125*(4), 257–259.

Naccache, L., et al. (2025). The global neuronal workspace theory of consciousness after COGITATE. *Neuroscience of Consciousness, 2025*(1), niae046.

Penrose, R., & Hameroff, S. (1996). Orchestrated reduction of quantum coherence in brain microtubules. *Mathematics and Computers in Simulation, 40*, 453–480.

Pothos, E. M., & Busemeyer, J. R. (2022). Quantum cognition. *Annual Review of Psychology, 73*, 749–778.

Prigogine, I., & Nicolis, G. (1977). *Self-Organization in Non-Equilibrium Systems.* Wiley.

Putnam, H. (1967). Time and physical geometry. *Journal of Philosophy, 64*(8), 240–247.

Reimann, M. W., et al. (2017). Cliques of neurons bound into cavities provide a missing link between structure and function. *Frontiers in Computational Neuroscience, 11*, 48.

Safron, A. (2020). An Integrated World Modeling Theory (IWMT) of consciousness: combining Integrated Information and Global Neuronal Workspace theories with the Free Energy Principle and active inference framework; toward solving the hard problem and characterizing agentic causation. *Frontiers in Artificial Intelligence, 3*, 30.

Skokowski, P. (2026). *Sensing Qualia: Solving the Hard Problem of Consciousness.* University of Chicago Press.

Stapp, H. (1993; 3rd ed. 2009). *Mind, Matter, and Quantum Mechanics.* Springer.

Tagliazucchi, E., et al. (2016). Large-scale signatures of unconsciousness are consistent with a departure from critical dynamics. *Journal of the Royal Society Interface, 13*(114), 20151027.

Tononi, G. (2004). An information integration theory of consciousness. *BMC Neuroscience, 5*, 42.

Tononi, G., et al. (2016). Integrated information theory: From consciousness to its physical substrate. *Nature Reviews Neuroscience, 17*(7), 450–461.

Von Neumann, J. (1932). *Mathematische Grundlagen der Quantenmechanik.* Springer.

Whitfield, J. D., Rodríguez-Rosario, C. A., & Aspuru-Guzik, A. (2010). Quantum stochastic walks: A generalization of classical random walks and quantum walks. *Physical Review A, 81*(2), 022323.

Wiseman, H. M., & Milburn, G. J. (2009). *Quantum Measurement and Control.* Cambridge University Press.

Zurek, W. H. (2009). Quantum Darwinism. *Nature Physics, 5*, 181–188.

### Tier 3: Preprints, Working Papers, and Speculative Extensions

Chalmers, D., & McQueen, K. (2021). Consciousness and the collapse of the wave function. arXiv:2105.02314.

Chen, Y., & Sanders, J. W. (2025). Consciousness as entropy reduction. arXiv:2510.06297.

Jha, D. K. (manuscript). Entropy driven awareness: Consciousness in the flow of time. PhilArchive.

Malloy, K. (forthcoming). ENAQT and radical pair spin coherence in microtubule tryptophan networks.

Malloy, K. (forthcoming). Quantitative viability of the radical pair transduction chain.

Malloy, K. (forthcoming). Quantum navigational advantage in evolved 3D maze controllers.

Malloy, K. (forthcoming). Topological disruption order under propofol sedation: A negative result.

Malloy, K. (2026). NFT formalization: Quantum stochastic walk formalism and complete positivity of discrete feedback loop.

Phillips, S., & Tsuchiya, N. (2024). Towards a (meta-)mathematical theory of consciousness. arXiv:2412.12179.

---

# Notes on Development

## Key Differences from v1.0 (book_draft_v1.md)

1. **Level B mechanism changed entirely.** Tryptophan excitonic ENAQT replaced by radical pair spin coherence, supported by computational simulation and Zadeh-Haghighi et al. 2026 experimental evidence.

2. **Negative results reported.** Both the ENAQT simulation failure (0.18% advantage) and the TDA temporal ordering failure are reported in full.

3. **Chapter 8 tells the honest path.** The story of excitonic → failure → radical pair → success makes the theory's responsiveness to evidence a structural feature of the book.

4. **Navigation benchmark rebuilt.** Chapter 10 tells the full story: original 2D result, failure against fair baselines, rebuild with matched budgets and paired evaluation, 3D/6D sweet spot, 90-maze confirmation of modest but systematic quantum navigational advantage.

5. **Structure reorganized by commitment level.** Chapters follow the A → B → C arc rather than the thematic grouping of v1.0, making the argument's separability performative rather than merely claimed.

6. **Level A / FEP relationship stated honestly.** Level A may be equivalent to active inference. NFT's distinctive contribution is at Level B.

7. **DeLancey engagement moved to Chapter 2** as the strongest foil for the structural difficulty argument.

8. **Possibility space moved to Level C.** No longer front-loaded before the reader has reason to engage with it.

9. **AI section restructured.** Four missing conditions cover quantum substrate, criticality, topological binding, and non-ergodicity. It is the conjunction, not any single condition, that matters.

10. **Preface includes reading guide** for casual readers and acknowledges negative results upfront.
