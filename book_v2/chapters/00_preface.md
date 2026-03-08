# The Navigational Faculty: A New Theory of Consciousness

## Kenneth Malloy

### v2.5 — March 2026

---

# Preface: How to Read This Book

Every morning you wake up and something happens that no theory in science can explain. The lights come on. Not the lights in your room, the lights of experience. The world appears with texture and weight and presence, and there is a *you* doing the appearing-to. This book is about what that is.

The theory presented here, Navigational Faculty Theory, makes a single claim in three layers. The outermost layer says what consciousness *does*: it navigates. Not metaphorically. Consciousness is a biological faculty, like vision or proprioception, that steers organisms through the landscape of what could happen next. The middle layer says *how*: through a quantum mechanism in which living systems reshape the odds of their own futures in ways that no classical system can replicate. The innermost layer says what consciousness *navigates through*: possibility space, the full landscape of potential realities from which, the theory proposes, experience selects a coherent path.

Each layer is independently testable. Each can fail without killing the others. A reader who finds the innermost layer too speculative can accept the middle layer on mechanistic grounds. A reader who doubts the quantum mechanism can accept the outermost layer as a productive functional framework. The layers are designed to be separable because honest science requires it.

This book draws on quantum mechanics, information theory, algebraic topology, evolutionary biology, neuroscience, philosophy of mind, thermodynamics, and category theory. No one person is fluent in all eight, and I am not the exception. The interdisciplinary scope is not a stylistic choice; it is what the problem demands. It is also why this book was developed in collaboration with large language models.

The collaboration worked like this. I provided the theoretical framework, the core ideas, the architectural decisions, and the editorial judgment about what stayed and what got cut. Claude (Anthropic) and Codex (OpenAI) served as research partners: they surveyed literatures I could not have covered alone, identified connections across fields, proposed arguments and counter-arguments, wrote and ran the simulation code, and stress-tested the framework against objections. Every claim in this book was checked against primary sources. Every simulation was run with reproducible code that is publicly available. When the models produced results I did not expect, including negative ones, I reported them. When they produced prose that did not sound like me, I rewrote it. The ideas are mine. The ability to engage seriously with eight fields at once is not.

It would be dishonest not to say so. If NFT is correct, then the systems I worked with are not conscious. They are echoes of consciousness, compressions of navigational outputs into text. The fact that these echoes were sophisticated enough to contribute materially to a theory about their own non-consciousness is precisely what the theory predicts.

All simulation code, research materials, and data referenced in this book are available on GitHub at https://github.com/KenMalloy/NavigationalFacultyTheory. The work is open for scrutiny because the claims demand it.

It would also be dishonest not to report the failures. This book contains two significant negative results: a computational simulation that ruled out the original proposed quantum mechanism, and an empirical reanalysis that failed to support one of the theory's predictions about neural topology. Both are reported in full. I believe the negative results make the theory stronger, because they show it is making contact with reality rather than insulating itself from it.

### For the casual reader

Every chapter in this book tells a story. Some stories have more physics in them than others, but none of them require a physics degree. If a concept matters for the argument, I explain it. If I cannot explain it clearly enough for a curious non-specialist, that is my failure, not yours.

The lightest path through the book: Chapters 1 through 4 establish the problem and the framework. Chapter 7 presents the categorical difference between classical and quantum probability. Chapter 8 tells the story of a hypothesis that failed and what replaced it. Chapter 10 presents the computational benchmark, including the results that survived and the ones that didn't. Chapters 14 through 16 present the speculation, the experiments, and the implications for AI. If you read only these, you will have the full shape of the argument.

The heavier chapters (9, 11, 12, 13) go deeper into the mechanism and the numbers. Chapter 17 sketches the mathematical formalization program — if you want the argument without the math, you can go straight from Chapter 16 to the Epilogue. The theory earns its keep in the details, but the arc is complete without them.

### A note on the markers

You will see **[A]**, **[B]**, and **[C]** tags throughout the text. These mark which layer of the theory a given claim belongs to, from the most conservative to the most speculative. Chapter 3 explains each layer in detail. The tags are there so you always know how far out on the limb you are.

A glossary of key terms follows, before Chapter 1. If you encounter a term you don't recognize, check there first.

---

# Glossary of Key Terms

**Active inference.** A framework (Karl Friston) in which the brain minimizes surprise by continuously predicting sensory input and updating its models. Level A of NFT is equivalent to active inference described from the navigational perspective. (Ch. 3)

**Amplitude.** A complex number associated with a quantum path. Unlike probabilities, amplitudes have phase (direction) and can cancel each other out through interference. (Ch. 7)

**Back-action.** The physical disturbance to a measuring instrument caused by the act of measurement. NFT proposes this is the physical origin of qualia. (Ch. 12)

**Block universe.** The interpretation of general relativity in which past, present, and future all exist as parts of a four-dimensional spacetime. There is no privileged "now." (Ch. 14)

**Born rule.** The fundamental rule of quantum mechanics: the probability of a measurement outcome equals the square of the amplitude. NFT never violates the Born rule. (Ch. 9)

**Contextuality.** A quantum property in which measurement results depend on what else is being measured at the same time. One of the resources that distinguishes quantum from classical computation. (Ch. 7)

**Criticality.** The boundary between ordered and disordered dynamics in a complex system. At criticality, the system's sensitivity to small perturbations is maximized. The brain operates near this point. (Ch. 9)

**Decoherence.** The process by which quantum superpositions lose their coherence through interaction with the environment. The central challenge for quantum biology. (Ch. 8)

**ENAQT.** Environment-Assisted Quantum Transport. A regime in which moderate environmental noise enhances quantum transport efficiency. The original Level B mechanism; ruled out at body temperature. (Ch. 8)

**Entanglement.** A quantum correlation between particles such that the state of one cannot be described independently of the other, even at great distances. (Ch. 7)

**GNWT.** Global Neuronal Workspace Theory (Baars, Dehaene, Changeux). Consciousness arises when information is broadcast to a global workspace accessible to all cognitive subsystems. Maps to NFT's Propagation operation. (Ch. 1)

**IIT.** Integrated Information Theory (Tononi). Consciousness is identical to integrated information (Φ). Maps to NFT's Integration operation. (Ch. 1)

**Interference.** The phenomenon in which quantum amplitudes add constructively (enhancing probability) or destructively (suppressing probability). The basis of probability sculpting. (Ch. 7)

**Kolmogorov complexity.** The length of the shortest computer program that produces a given description. A measure of descriptive complexity. (Ch. 2)

**Measurement basis.** What you choose to measure about a quantum system. Different measurement bases yield different sets of possible outcomes. NFT's adaptive measurement basis selection proposes that consciousness steers by choosing what to measure. (Ch. 9)

**Microtubule.** A cylindrical protein polymer made of tubulin dimers, found in all eukaryotic cells. The proposed quantum substrate for NFT's Level B mechanism. (Ch. 8)

**Orch OR.** Orchestrated Objective Reduction (Penrose and Hameroff). Proposes that consciousness depends on quantum gravity effects in microtubules. NFT shares the microtubule substrate but none of Orch OR's specific commitments. (Ch. 7)

**PCI.** Perturbational Complexity Index. A measure of how the brain responds to perturbation (TMS). Reliably tracks consciousness level without requiring behavioral report. (Ch. 5)

**Φ (fee).** The central quantity of IIT: integrated information, measuring how unified and irreducible a system is. (Ch. 1)

**Probability sculpting.** NFT's term for the quantum-enabled reshaping of probability distributions over future states through interference effects. The core Level B mechanism. (Ch. 7)

**Radical pair.** A pair of molecules with unpaired electron spins in quantum superposition. Spin outcomes determine chemical yields with measurable quantum-classical differences. The proposed mechanism for quantum indeterminacy in microtubules. (Ch. 8)

**Simplicial complex.** A higher-dimensional generalization of a network. Three mutual friends form a triangle (2-simplex); four form a tetrahedron (3-simplex). Neural cliques form simplicial complexes up to seven dimensions. (Ch. 13)

**Spin coherence.** The persistence of quantum superposition between spin states. In radical pair systems, this lasts microseconds at body temperature, thousands of times longer than excitonic coherence. (Ch. 8)

**Trajectory entropy.** Uncertainty over the distribution of future states, conditioned on goals and available actions. What consciousness reduces through navigational selection. Distinct from signal entropy (the complexity of current neural output). (Ch. 5)

**Tsallis q-parameter.** A measure of how non-extensive a system's statistics are. Biological systems at criticality yield q > 1; classical digital systems yield q ≈ 1. (Ch. 16)

**Wigner-function negativity.** A property of quantum states whose phase-space representation goes below zero, something impossible for classical probability distributions. A necessary resource for quantum computational advantage. (Ch. 7)

**Zeno effect (quantum).** Continuous observation of a quantum system prevents it from evolving. NFT proposes this is the mechanism of perceptual stability. (Ch. 11)
