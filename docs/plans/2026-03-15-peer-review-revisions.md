# Book v2.1 Peer Review Revisions Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address convergent peer review feedback from 15 discipline-specific reviewers, prioritized by impact and feasibility.

**Architecture:** Prose revisions to `book_draft_v2.md` (master file) and corresponding chapter files in `book_v2/chapters/`. Each task is a discrete editorial pass on a specific concern. Tasks are ordered: (1) fixes that prevent credibility damage first, (2) substantive additions second, (3) polish third.

**Severity key:** 🔴 = credibility risk if unfixed, 🟡 = significantly strengthens the book, 🟢 = nice-to-have polish

---

## Tier 1: Credibility Fixes (overclaiming, methodological issues)

These are the changes that prevent reviewers from dismissing the book. They are primarily about *softening language* and *adding caveats* — fast to implement, high impact.

### Task 1: Downgrade Chapter 10 Proof Language 🔴

**Why:** 6/15 reviewers flagged overclaiming. The GA optimizes parameters FOR the quantum condition then hands them to controls — an asymmetric comparison. "Provably unreachable" and "categorical advantage" are not warranted without separate per-condition optimization. A classical wall-following heuristic would likely solve both mazes.

**Files:**
- Modify: `book_draft_v2.md` (lines 23, 489, 541, 583, 591, 607, 611)
- Modify: `book_v2/chapters/10_navigation_proof.md`
- Modify: `book_v2/chapters/00_preface.md` (line 23 reference to "computational proof")

**Changes:**

1. Line 23 (Preface): "computational proof that the mechanism works" → "computational demonstration that the mechanism can produce navigational advantages"

2. Line 489 (Chapter 10 opening): Replace "produces navigational advantages over all classical and non-adaptive quantum controls — including, on one maze, a categorical advantage where the quantum agent finds solutions that no control condition can reach" → "produces navigational advantages in a proof-of-principle demonstration — including, on one maze, solutions that no control condition achieved under the same evolved parameters"

3. Line 541: "provably unreachable by all three control conditions" → "not achieved by any control condition under these parameters"

4. Line 583: "provably unreachable by controls" → "not reached by any control"

5. Line 591: "regardless of how well their parameters are optimized" → DELETE this clause. Replace with: "under the same parameter set evolved for the quantum condition. A stronger test — evolving parameters independently per condition — is needed to establish that no classical parameterization can match the quantum agent."

6. Lines 607-611 ("What the Simulations Do and Do Not Prove"): Add a new paragraph after "These are empirical questions...":

> **A methodological caveat.** The genetic algorithm in these simulations optimized parameters for the quantum+adaptive condition. The same parameters were then applied to all control conditions. This means the controls received parameters tuned for a different dynamical regime — parameters mismatched to their own dynamics. A stronger demonstration would evolve parameters independently for each condition and compare the best achievable performance of each. Until that comparison is done, the results demonstrate that the quantum feedback loop provides a richer optimization landscape for the GA to exploit, which is a weaker claim than "quantum dynamics provide an inherent computational advantage." The categorical separation (24% vs 0% on Maze 1) is suggestive but not conclusive. We report it as a proof of principle, not a proof of quantum advantage.

7. Retitle the chapter: "The Higher-Dimensional Navigation Proof" → "The Higher-Dimensional Navigation Demonstration"

---

### Task 2: Temper Zadeh-Haghighi / Anesthesia Evidence Claims 🔴

**Why:** 5/15 reviewers flagged overclaiming. The isotope effect demonstrates radical pair chemistry in microtubules, not consciousness-relevant navigation. The ROS/oxidative stress alternative is unaddressed. Propofol and xenon work through different mechanisms and are mixed together.

**Files:**
- Modify: `book_draft_v2.md` (lines ~407-420, ~739-755, ~821)
- Modify: `book_v2/chapters/08_honest_path.md`
- Modify: `book_v2/chapters/15_experimental_program.md`

**Changes:**

1. Line 407: "direct experimental evidence that radical pair reactions occur in microtubules" → "direct experimental evidence that radical pair chemistry occurs in tubulin — though the gap between 'radical pairs exist here' and 'radical pairs do computational work relevant to consciousness' remains substantial"

2. After line 411, add new paragraph:

> **The oxidative stress alternative.** The [TrpH⁺...O₂⁻] radical pair is a reactive oxygen species pathway. ROS in microtubules are heavily studied in the context of oxidative damage, aging, and neurodegeneration. The most parsimonious interpretation of the Zadeh-Haghighi result is that radical pairs participate in tubulin redox chemistry — not that they participate in consciousness. The isotope effect on polymerization is a structural/mechanical observation; it does not by itself demonstrate that radical pair chemistry in assembled microtubules modulates neural signaling or conscious processing. NFT predicts that the radical pair chemistry IS relevant to navigation, but this prediction is not yet confirmed. The isotope effect establishes the substrate; it does not establish the function.

3. Lines 739-755 (Chapter 15, anesthesia predictions): Add pharmacological specificity:

> **Pharmacological caveat.** The anesthesia evidence mixes agents with different mechanisms: xenon acts primarily through NMDA receptor antagonism, propofol through GABA-A potentiation, and neither has established direct effects on microtubule radical pair chemistry. The isotope effects (xenon, magnesium) are consistent with radical pair involvement in some aspect of neural function, but the bridge from "radical pairs are involved in anesthetic pharmacology" to "radical pairs in microtubules are the mechanism of consciousness" passes through several uncontrolled steps. Future work should map anesthetic mechanisms to specific radical pair sites in microtubules and test predictions for agents with known microtubule-disrupting effects (colchicine, vinblastine) versus agents that act through unrelated mechanisms.

---

### Task 3: Fix the State-Dependent Lindblad Formalism 🔴

**Why:** 4/15 reviewers flagged this. The nonlinear L_k(ρ) equation breaks complete positivity, trace preservation, and semigroup properties. But the actual physics (and the code) implements a sequential classical-quantum feedback loop, which is fine. Presentation problem, not physics problem.

**Files:**
- Modify: `book_draft_v2.md` (lines ~966-970, ~1000)
- Modify: `book_v2/chapters/17_formalization.md`

**Changes:**

Replace lines 966-970 with:

> For NFT's adaptive measurement thesis, the measurement basis depends on classical variables — the current conformational state of the protein, which is updated by previous measurement outcomes. This is a classical-quantum hybrid feedback loop: each radical pair event is computed with a standard (linear, completely positive) quantum channel, and the classical outcome updates the parameters for the next channel. The sequential process is:
>
> 1. Evolve the radical pair under Hamiltonian H(θ) where θ is the current conformation
> 2. Apply Haberkorn recombination (standard Lindblad dissipator)
> 3. Record the singlet/triplet yield (classical measurement outcome)
> 4. Update θ based on the outcome (classical parameter update)
> 5. Return to step 1 with the new H(θ)
>
> Each individual step preserves complete positivity. The total evolution is a valid quantum instrument conditioned on classical parameters. This is standard quantum feedback control (Wiseman and Milburn) and is physically unproblematic.
>
> The continuous-time approximation — a state-dependent Lindblad master equation where L_k depends on ρ itself — is sometimes used as a mathematical shorthand but introduces nonlinearity that breaks the GKSL theorem's guarantees. NFT's physical mechanism does not require this continuous approximation. The sequential measurement-update cycle is the correct formalization.

Update line 1000 accordingly: remove "Whether the QSW formalism can be extended to accommodate state-dependent Lindblad operators while preserving the mathematical properties" and replace with: "Whether the sequential quantum-classical feedback loop can be given a compact continuous-time representation while preserving complete positivity is a mathematical convenience question, not a physical one. The discrete-time formulation is well-defined."

---

### Task 4: Steelman DeLancey, Drop the Cheap Shot 🟡

**Why:** 3/15 reviewers (including thermodynamics) called "Shannon ruler to a Tsallis world" a cheap shot. DeLancey argues Kolmogorov incompressibility (about individual objects), not Shannon entropy (about ensembles). The temporal critique is much stronger and doesn't need the zinger.

**Files:**
- Modify: `book_draft_v2.md` (lines ~113-133)
- Modify: `book_v2/chapters/02_structurally_hard.md`

**Changes:**

1. Delete line 133 ("DeLancey brought a Shannon ruler to a Tsallis world.")

2. Rewrite the DeLancey section (~lines 113-132) to:
   - Lead with the temporal critique (DeLancey's framework has no treatment of temporal experience — this is the strong argument)
   - Acknowledge that Kolmogorov incompressibility is about individual objects, not ensemble statistics, and that DeLancey's argument does not depend on which entropy measure you use
   - Note that the AIT evolution (Bennett → Gell-Mann/Lloyd → Zenil → Tsallis-Chaitin) is relevant context but does not invalidate DeLancey's specific claim about incompressibility
   - State that NFT's disagreement with DeLancey is conditional on Level B: if consciousness requires genuine indeterminacy, then incompressibility of descriptions is insufficient; but this critique only has force if Level B is correct, so it cannot independently motivate Level B

---

## Tier 2: Substantive Additions (filling gaps, adding missing content)

These require writing new paragraphs or sections. Higher effort, but address the convergent concerns about missing substance.

### Task 5: Add the Transduction Chain Estimate 🔴

**Why:** The single most convergent concern across ALL reviews. The chain from radical pair yield → protein conformation → ion channel → neural firing → network behavior is unquantified. Even order-of-magnitude estimates would either strengthen or honestly kill Level B.

**Files:**
- Modify: `book_draft_v2.md` — new section in Chapter 9, after the criticality amplification section (~line 437)
- Modify: `book_v2/chapters/09_how_sculpting_works.md`

**New section: "The Transduction Chain: An Order-of-Magnitude Estimate"**

Content to include:
- Radical pair yield difference: 12.7% (from simulation)
- Number of radical pair events per tubulin dimer per millisecond (estimate from ROS encounter rates)
- Conformational force from differential product formation vs thermal noise (kT ~ 4 pN·nm at 310K)
- Number of tubulin dimers per microtubule (~13 protofilaments × ~1000 dimers = ~13,000)
- Number of microtubules per neuron (estimates vary: hundreds to thousands)
- Aggregate statistical bias at the single-microtubule level over neural timescales (1-10 ms)
- Criticality amplification factor (51x at σ=1.0)
- Compare final signal estimate to known ion channel noise amplitudes

**Honest framing:** "If these numbers work — if the aggregate radical pair bias exceeds the thermal noise floor at the neural timescale — Level B survives quantitatively. If they do not, Level B is a hypothesis about quantum chemistry rather than a theory of consciousness. We present the estimates; the reader can judge."

**Note to author:** This calculation may need to be done computationally before writing. If the numbers kill Level B, we report that honestly, consistent with the book's methodology.

---

### Task 6: Separate "Quantum Biology Substrate" from "Consciousness Mechanism" in Predictions 🟡

**Why:** 4/15 reviewers noted that most "discriminative" predictions test quantum biology, not consciousness. Predictions 1, 3, 4, 5 would demonstrate radical pair chemistry in microtubules without demonstrating it constitutes consciousness.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 15, lines ~821-855)
- Modify: `book_v2/chapters/15_experimental_program.md`

**Changes:**

Reorganize the discriminative predictions into two categories:

**Category A: Tests of the Quantum Biology Substrate** (establishes the physical platform)
- Radical pair isotope effects on neural function (not consciousness specifically)
- ENAQT optimum in radical pair dynamics
- Entanglement witness in radical pair systems
- Anti-Zeno spectral signature

**Category B: Tests of the Consciousness Link** (tests whether the substrate matters for consciousness)
- The AI discrimination test (Level 2 vs Level 3) — genuinely discriminative
- Back-action evasion zombie — genuinely discriminative
- NEW: Within-state conscious access paradigm — test whether radical pair disruption selectively impairs conscious access while leaving unconscious processing intact (addresses the cognitive science reviewer's concern)
- NEW: Isotope effects on consciousness thresholds specifically (not just neural function) — measured by PCI or other consciousness-specific markers

Add explicit acknowledgment: "Category A predictions test whether the physical substrate exists. Category B predictions test whether the substrate matters for consciousness. Both are necessary; neither alone is sufficient."

---

### Task 7: Acknowledge Level A as Interpretive Framework, Not Independent Claim 🟡

**Why:** 5/15 reviewers converge: Level A is active inference redescribed. The manuscript already acknowledges this (Chapter 3) but still trades on Level A language as if it's novel. The four operations map onto existing functional decompositions.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 3, ~lines 155-170; Chapter 4, ~lines 195-210)
- Modify: `book_v2/chapters/03_testability.md`
- Modify: `book_v2/chapters/04_navigation.md`

**Changes:**

1. Chapter 3: Strengthen the honest framing. After the active inference acknowledgment, add:

> To be direct: Level A may not be an independent scientific claim. It may be a vocabulary — a way of organizing the functional insights of active inference, IIT, and GNWT under a navigational metaphor. If so, its value is pedagogical and architectural rather than empirical. It provides the frame within which Level B's quantum mechanism makes sense, but it does not by itself generate predictions that active inference does not already generate. The reader who finds Level A to be "just active inference in a new coat" is not wrong. The reader who finds the coat useful for seeing how IIT and GNWT fit together may also not be wrong. The distinctive science is at Level B.

2. Chapter 4: After the four operations, add:

> A reader familiar with active inference will recognize these operations: generation is stochastic sampling in a generative model, selection is policy selection under expected free energy, integration is IIT's Φ requirement, and propagation is GNWT's broadcasting. The navigational language organizes these established components under a common frame. What it adds — and what justifies the new vocabulary — is the claim that generation is not merely stochastic sampling but physical indeterminacy (Level B), and that selection is not merely Bayesian inference but quantum measurement with structured back-action. Without Level B, the four operations are a relabeling. With Level B, they describe a genuinely different physical process.

---

### Task 8: Reframe Adaptive Measurement as Research Program, Not Settled Mechanism 🟡

**Why:** 4/15 reviewers flagged that adaptive measurement basis selection is NFT's most important and least derived mechanism. The manuscript presents it with more confidence than the evidence warrants. The physics is plausible but the control law has not been derived from first principles.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 9, ~lines 441-480)
- Modify: `book_v2/chapters/09_how_sculpting_works.md`

**Changes:**

After the feedback loop description, add:

> **Status of this mechanism.** The adaptive measurement basis selection idea is NFT's most distinctive contribution to Level B — and its least derived one. The feedback loop is physically plausible: radical pair outcomes do produce conformational changes, and conformational changes do alter the electromagnetic environment of subsequent radical pair events. But the specific control law — which conformational changes, driven by which outcomes, alter which Hamiltonian parameters, producing which navigational effects — has not been derived from first principles. It has been demonstrated computationally in a toy model (Chapter 10) but not in a biophysically realistic microtubule simulation.
>
> The honest framing: adaptive measurement basis selection is a *research program*, not a settled mechanism. The computational demonstration shows it can work in principle. The biological plausibility argument shows it is not physically impossible. What is missing is the derivation — a first-principles account of how specific tubulin conformational states modulate specific radical pair Hamiltonians to produce specific navigational biases. This derivation is the single most important piece of theoretical work remaining for Level B.

---

### Task 9: Downsize the Cambrian Claim, Engage Comparative Cognition 🟡

**Why:** 3/15 reviewers (evolution, neuroscience, philosophy) flagged the Cambrian claim as untestable just-so storytelling. Cephalopods and insects are immediate counterexamples to the microtubule complexity prediction.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 6, ~lines 289-300)
- Modify: `book_v2/chapters/06_evolutionary_case.md`

**Changes:**

1. Reduce the Cambrian section to two sentences:

> The temporal coincidence between the evolution of complex microtubule networks in animals and the Cambrian radiation is suggestive but untestable as a historical hypothesis. We note it without claiming explanatory force.

2. After the "behavioral flexibility tracks microtubule complexity" prediction, add:

> **Comparative challenges.** This prediction faces immediate complications from comparative cognition. Cephalopods exhibit extraordinary behavioral flexibility — tool use, problem solving, observational learning — with nervous system architecture radically different from vertebrates. Insects (particularly hymenopterans) show remarkable behavioral flexibility with very small nervous systems. The comparative cognition literature has moved strongly toward recognizing that behavioral flexibility is multiply realized across nervous system architectures. Any single structural variable — brain size, neuron count, or microtubule complexity — is likely to face exceptions. The prediction may need to be qualified to "within a given clade" rather than across all eukaryotes, or reformulated as a partial correlation controlling for other variables.

---

### Task 10: Add Missing Neuroscience Evidence (PCI, Massimini) 🟡

**Why:** The neuroscience reviewer noted significant omissions: Perturbational Complexity Index, Massimini group's work on cortical effective connectivity breakdown, Tagliazucchi on criticality and consciousness.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 5, after empirical evidence section ~lines 229-235)
- Modify: `book_v2/chapters/05_entropic_current.md`

**Changes:**

Add after the existing empirical evidence paragraph:

> The Perturbational Complexity Index (PCI), developed by Casali and colleagues, operationalizes consciousness level by measuring how the brain responds to perturbation — combining TMS stimulation with algorithmic complexity of the evoked EEG response. PCI reliably tracks conscious level across wakefulness, sleep, anesthesia, and disorders of consciousness without requiring behavioral report. A system at criticality should show maximal PCI; departures from criticality should reduce it. This maps directly onto NFT's claims: at criticality, the navigational system has maximal flexibility; away from criticality, navigation is impaired.
>
> The Massimini group's complementary finding — that loss of consciousness is characterized by breakdown of cortical effective connectivity, the brain's inability to sustain complex, differentiated responses to perturbation — is precisely what NFT would predict from loss of criticality-mediated amplification. Tagliazucchi and colleagues provide direct evidence that the brain shifts away from criticality during loss of consciousness in sleep and anesthesia, grounding the criticality claim in specific empirical measurements rather than general theoretical arguments.

---

## Tier 3: Structural/Polish Fixes

### Task 11: Specify Entropy Taxonomy More Precisely 🟢

**Why:** 3/15 reviewers said "entropy" is doing too many jobs. The signal/trajectory distinction is good but the formal definition of trajectory entropy is missing.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 5, ~lines 229-245)
- Modify: `book_v2/chapters/05_entropic_current.md`

**Changes:**

After the signal/trajectory distinction, add a precise definition:

> **Trajectory entropy defined.** We define trajectory entropy as the conditional Shannon entropy H(X_{t+τ} | X_t, π) — the uncertainty over future states X at horizon τ, given the current state X_t and the organism's policy π. A classical Bayesian agent reduces this quantity through prediction and planning. NFT's Level B claim is that a quantum-coupled agent reduces it more efficiently under matched biological constraints — same state space, same computational resources, same noise floor. The classical baseline for this claim can in principle be computed using active inference's expected free energy decomposition, where the epistemic term (information gain) maps directly onto trajectory entropy reduction. The quantum claim is that interference-mediated probability sculpting exceeds this classical baseline. This is a testable quantitative claim, though the comparison has not yet been performed.

---

### Task 12: Hedge Criticality Claims with Universality Class 🟢

**Why:** Thermodynamics reviewer noted that "criticality" is not generic — universality class matters for amplification properties.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 9, ~lines 431-437)
- Modify: `book_v2/chapters/09_how_sculpting_works.md`

**Changes:**

After the criticality amplification result, add:

> **Universality class matters.** The 51-fold amplification is a result from a specific computational model. In critical phenomena, amplification properties (susceptibility exponents, scaling laws) depend on the universality class of the phase transition. Whether the brain's criticality is best described as a continuous phase transition (mean-field? Ising? directed percolation?), self-organized criticality, or Griffiths-phase quasi-criticality affects the quantitative predictions. SOC systems fluctuate around the critical point rather than sitting precisely on it, which means the 51-fold amplification is a peak value and the average amplification would be lower. The manuscript treats criticality as proximity to a generic amplification regime; a more precise treatment would identify the universality class and derive the scaling exponent.

---

### Task 13: Reframe Negative Conditional Entropy as Prediction, Not Marker 🟢

**Why:** 3/15 reviewers noted the wedge argument is deployed as if entanglement is established when it is not.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 7, ~lines 333-345)
- Modify: `book_v2/chapters/07_categorical_difference.md`

**Changes:**

Reframe the section: "If the radical pair substrate sustains entanglement between distinct subsystems — which is the empirical question posed by Prediction 4 (entanglement witness) — then the navigator would have access to information-theoretic resources that no classical system can replicate. The negative conditional entropy wedge is a *prediction* about what should be found if Level B is correct, not a feature that has been demonstrated in the biological substrate."

Specify subsystems: "The relevant bipartite decomposition remains to be identified: two radical pairs in adjacent tubulin dimers? A radical pair and the conformational degree of freedom it is embedded in? The choice has physical consequences for whether entanglement is plausible on the relevant timescales."

---

### Task 14: Add Interpretation Sensitivity Note (Placeholder for Appendix J) 🟢

**Why:** Philosophy reviewer says Appendix J (quantum interpretations) is "not optional." Full appendix is beyond scope of this revision pass, but a note in Chapter 14 is needed.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 14, after QBism section ~line 810)
- Modify: `book_v2/chapters/14_possibility_space.md`

**Changes:**

Add a section: "### Interpretation Sensitivity"

> NFT's coherence depends on which interpretation of quantum mechanics it presupposes, and this dependence is not fully resolved in this book. Under Everett (many worlds), there is no collapse and thus no selection — NFT would need to be reframed as branch-selection rather than wavefunction collapse. Under Bohm, outcomes are determined by hidden variables and selection is illusory. Under Copenhagen, measurement is primitive and consciousness-as-measurement risks circularity. Under QBism, measurement is subjective updating by an agent, which is closest to NFT's picture but raises the question of what constitutes an "agent."
>
> NFT at Level B is most naturally compatible with QBism and with certain objective collapse theories. It is least compatible with Everettian and Bohmian interpretations. A full interpretation-by-interpretation analysis is the subject of Appendix J [to be developed]. For now, we note that Level B's empirical predictions — the discriminative experiments of Chapter 15 — do not depend on the interpretive question. The predictions are about measurable quantities (isotope effects, entanglement witnesses, behavioral differences between quantum and classical substrates) that are interpretation-neutral. The interpretive question affects the *ontological meaning* of the results, not the results themselves.

---

### Task 15: Acknowledge the Philosophy Dilemma (Classical Controller vs Quantum Substrate) 🟡

**Why:** Philosophy reviewer identified this as the deepest vulnerability. If classical neural computation selects the measurement basis, the agency is classical and the hard problem reappears there. If the loop is fully quantum, nonlinear QM problems arise.

**Files:**
- Modify: `book_draft_v2.md` (Chapter 9, after the feedback loop, ~line 470)
- Modify: `book_v2/chapters/09_how_sculpting_works.md`

**Changes:**

Add after the "Reading and Writing as One Process" section:

> **The controller question.** A philosophical objection must be confronted directly: if classical neural computation selects the measurement basis, then the agency of the navigator is classical. The quantum component provides raw material (indeterminacy, interference, back-action), but the steering is classical. And if the steering is classical, the hard problem reappears at the classical level: why is there something it is like to be the classical process that selects measurement bases?
>
> NFT's response is that the classical/quantum distinction in the feedback loop is not as clean as the objection assumes. The "classical controller" is itself a neural network operating at criticality — a system whose dynamics are shaped by the aggregate of previous quantum measurement outcomes. The controller is not independent of the quantum substrate; it is constituted by its history of interactions with it. The organism is not a classical captain steering a quantum ship. It is a system in which classical and quantum dynamics are so interleaved that attributing agency to one level rather than the other may be a category error.
>
> Whether this response is adequate is an open philosophical question. It is possible that the hard problem genuinely reappears at the classical level and that NFT has relocated rather than addressed it. We acknowledge this possibility. The back-action thesis (Chapter 12) proposes that phenomenal experience is the quantum component — the structured perturbation during measurement — not the classical component. But whether the classical selection process that determines *which* perturbation occurs is itself conscious remains unresolved. This is the deepest question the theory faces, and we do not pretend to have answered it.

---

## Task Execution Order

**First pass (credibility — do these before anything else):**
1. Task 1: Downgrade Chapter 10 proof language
2. Task 2: Temper Zadeh-Haghighi / anesthesia claims
3. Task 3: Fix state-dependent Lindblad formalism
4. Task 4: Steelman DeLancey

**Second pass (substance — requires some new writing):**
5. Task 7: Level A as interpretive framework
6. Task 8: Reframe adaptive measurement as research program
7. Task 6: Separate quantum biology from consciousness predictions
8. Task 9: Downsize Cambrian, add comparative cognition
9. Task 15: Acknowledge the controller dilemma
10. Task 10: Add PCI and Massimini evidence

**Third pass (polish):**
11. Task 11: Entropy taxonomy
12. Task 12: Criticality universality class
13. Task 13: Negative conditional entropy as prediction
14. Task 14: Interpretation sensitivity note

**Deferred (requires computation, not just prose):**
15. Task 5: Transduction chain estimate — THIS IS THE MOST IMPORTANT TASK but requires actual calculation before writing. Should be done as a separate computational session, then results written into Chapter 9.

---

## Post-Revision Checklist

After all tasks complete:
- [ ] Search for remaining instances of "provably," "categorical advantage," "proves" in overclaiming contexts
- [ ] Verify all chapter files in `book_v2/chapters/` match the master `book_draft_v2.md`
- [ ] Ensure negative results (ENAQT, TDA) are still prominently reported
- [ ] Verify [A], [B], [C] tags are consistent with the revised claims
- [ ] Check that the Preface reading guide still accurately describes what each chapter contains
