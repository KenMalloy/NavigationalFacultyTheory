---

## Chapter 17: The Formalization Horizon

A theory without mathematics is a metaphor. This chapter sketches the mathematical framework that would make NFT fully rigorous. It is also honest about how far that program has actually progressed, which is: not far enough.

### The Boolean Hypercube

A Boolean hypercube of dimension *N* is the graph whose vertices are binary strings x ∈ {0,1}^N and whose edges connect pairs differing in exactly one bit. This is the canonical state space for any system composed of N binary switches.

The hypercube is not novel: it is latent in NK fitness landscapes, Boolean gene regulatory networks, and quantum information. In evolutionary biology, genotypes are explicit bitstrings and mutations are single-bit flips. In Boolean networks, the whole-cell gene expression state is an N-bit vector. In quantum information, the computational basis of N qubits indexes the hypercube vertices.

Santiago-Alarcon and colleagues (2020, *Journal of the Royal Society Interface*) explicitly defined genotypes as binary strings, neighborhoods as single-step mutations, and compared classical and quantum walks for exploring genotype networks, a direct precedent for quantum navigation on biological state spaces.

NFT proposes that possibility space admits hypercube structure when the relevant degrees of freedom are identified and discretized. For microtubule systems, each tubulin subunit's conformational state (or radical pair spin state) can be represented as a binary variable, and the system's configuration space becomes a Boolean hypercube whose dimension scales with the number of relevant subunits.

### The Quantum Stochastic Walk

The mathematical backbone is a framework called a quantum stochastic walk (QSW). Think of it as a single equation with a dial. Turn the dial one way and the system behaves like a classical random walk, each step independent and diffusive. Turn it the other way and the system behaves like a quantum walk, with interference between paths. At intermediate settings, the system does something neither purely classical nor purely quantum. That intermediate regime is where NFT's probability sculpting lives. The dial's setting maps directly onto the γ/κ parameter from Chapter 8: the ratio of quantum coherence to environmental noise.

The adaptive measurement thesis adds a feedback loop: the outcome of each quantum measurement changes what gets measured next. The protein's current shape determines the quantum evolution; the quantum outcome changes the protein's shape; the new shape determines the next evolution. This cycle repeats continuously. Each individual step is standard quantum mechanics. The feedback loop is standard control theory (Wiseman and Milburn, 2009). Nothing exotic is required.

One thing worth noting, because it matters for whether the mechanism is physically legitimate: there is a temptation in quantum biology to write down continuous-time equations where the measurement operator depends on the system's own state. This looks elegant but breaks a foundational guarantee of quantum mechanics called complete positivity. The math stops being physically valid. NFT does not require this shortcut. The actual mechanism is a discrete cycle: evolve the radical pair, record the outcome, update the protein conformation, repeat. Each step is a standard quantum operation. The full sequence is standard quantum feedback control. The formalism is well-defined, and the computational simulations implement exactly this cycle. The formal details are developed in [Malloy 2026].

### The Negative Conditional Entropy Wedge

The categorical difference between quantum and classical information resources was introduced in Chapter 7. The formal question that follows from it is specific: does the microtubule radical pair network exhibit negative conditional entropy under physiological conditions? If so, the navigator has access to information-theoretic resources that no classical system can replicate. This question is in principle answerable with current experimental techniques applied to radical pair spin state tomography.

### The Multi-Scale Synthesis

The full formalization needs to connect three scales of description — like a map that works at street level, city level, and continental level simultaneously. Each scale needs its own mathematics, and the scales need to talk to each other.

At the bottom, quantum mechanics. Hilbert space, measurement operators, back-action: the language of radical pair spin states. At the middle, geometry. Conscious trajectories follow shortest paths on curved landscapes defined by neural connectivity, and the natural description is Riemannian. At the top, category theory — the claim that IIT, GNWT, and the quantum substrate are subsystems of one architecture translates into a precise statement about structural relationships between mathematical categories.

Phillips and Tsuchiya's demonstration that IIT's axioms derive from a universal mapping property suggests that category theory is not an arbitrary mathematical choice but a natural language for the structural requirements of consciousness.

### What Remains

NFT at present is more precise than a metaphor but less precise than a mathematical theory. The gap is real.

Whether the sequential quantum-classical feedback loop can be given a compact continuous-time representation while preserving complete positivity is a mathematical convenience question, not a physical one; the discrete-time formulation is well-defined. Whether the multi-scale synthesis can be made rigorous, deriving Φ, broadcasting dynamics, and radical pair measurement from a single navigational principle, is the most important area of future theoretical work.

A framework that honestly reports where its mathematics ends is more trustworthy than one that pretends the mathematics is complete. The formalization horizon is visible. Whether it can be reached is the work ahead.
