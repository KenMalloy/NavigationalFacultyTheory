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

> **Deep dive: the QSW formalism.** The QSW framework provides a Lindblad master equation interpolating between coherent quantum walks and classical random walks on the same graph: ρ̇ = −i[H, ρ] + Σ_k (L_k ρ L_k† − ½{L_k†L_k, ρ}). With walk Hamiltonian H_walk = γA (adjacency matrix), potential landscape H_pot = Σ_x E(x)|x⟩⟨x|, and local dephasing operators L_j = √κ Z_j. The sequential feedback process: (1) evolve the radical pair under Hamiltonian H(θ), where θ is the current conformation; (2) apply Haberkorn recombination (standard Lindblad dissipator); (3) record the singlet/triplet yield; (4) update θ based on the outcome; (5) return to step 1. Each step is a standard, linear, completely positive quantum channel. A continuous-time approximation writing L_k as a function of ρ introduces nonlinearity that breaks GKSL guarantees; NFT's physical mechanism does not require this approximation. The discrete-time formulation is well-defined.

### The Negative Conditional Entropy Wedge

The categorical difference between quantum and classical information resources was introduced in Chapter 7. The formal question that follows from it is specific: does the microtubule radical pair network exhibit negative conditional entropy under physiological conditions? If so, the navigator has access to information-theoretic resources that no classical system can replicate. This question is in principle answerable with current experimental techniques applied to radical pair spin state tomography.

### The Multi-Scale Synthesis

The full formalization needs to connect three scales of description, like a map that works at street level, city level, and continental level simultaneously. Each scale needs its own mathematics, and the scales need to talk to each other.

At the **microscale**, quantum mechanics (Hilbert space): measurement and back-action in radical pair spin states. At the **mesoscale**, geometry (Riemannian manifolds): conscious trajectories following shortest paths on curved landscapes defined by neural connectivity. At the **macroscale**, structural mathematics (category theory): the claim that IIT, GNWT, and the quantum substrate are subsystems of one architecture translates into a precise statement about structural relationships between mathematical categories.

Phillips and Tsuchiya's demonstration that IIT's axioms derive from a universal mapping property suggests that category theory is not an arbitrary mathematical choice but a natural language for the structural requirements of consciousness.

### What Remains

NFT at present is more precise than a metaphor but less precise than a mathematical theory. The gap is real.

Whether the sequential quantum-classical feedback loop can be given a compact continuous-time representation while preserving complete positivity is a mathematical convenience question, not a physical one; the discrete-time formulation is well-defined. Whether the multi-scale synthesis can be made rigorous, deriving Φ, broadcasting dynamics, and radical pair measurement from a single navigational principle, is the most important area of future theoretical work.

A framework that honestly reports where its mathematics ends is more trustworthy than one that pretends the mathematics is complete. The formalization horizon is visible. Whether it can be reached is the work ahead.
