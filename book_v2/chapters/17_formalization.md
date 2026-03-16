## Chapter 17: The Formalization Horizon

A tungsten filament lightbulb can be on or off. Two states, one or the other, and nothing in between. Now add a second bulb. Both off, first on, second on, both on. The four combinations act as the corners of a square. Flip one bulb and you move to the next corner. Add a third bulb and the square becomes a cube. A fourth bulb and the cube becomes something you can't picture anymore, but you can still walk it. One flip, one step, corner to neighboring corner. Mathematicians call this a Boolean hypercube, and a walk along its edges is a journey through possibility.

The hypercube shows up everywhere. In evolutionary biology, each gene is a switch, each mutation flips one, and the fitness landscape is a walk across its surface. Santiago-Alarcon and colleagues (2020) compared classical and quantum walks on genotype networks. In quantum computing, every possible state of N qubits is a corner of the same shape.

Now scale it to a microtubule. Each tubulin subunit has a conformational state (the physical shape the protein is sitting in at that moment) that can be represented as a binary variable, one shape or the other. A single microtubule has roughly 13,000 subunits. The configuration space is a Boolean hypercube with 13,000 dimensions. You cannot picture it, but you can walk it. And the question that matters for NFT is *how* you walk it.

A classical walker steps along one edge at a time. It explores by diffusion, one flip, then another, a random walk through the corners. A quantum walker spreads across multiple paths simultaneously, and the paths interfere. Some corners are reinforced, others suppressed. The destination is shaped by interference. That is probability sculpting, written in geometry.

### The Quantum Stochastic Walk

A quantum stochastic walk (QSW) is a single equation with a dial. At one extreme, pure classical diffusion. The walker stumbles from corner to corner with no memory and no interference. Probability theorists have been calling this a drunkard's walk since 1905, which may be the most honest name in mathematics. At the other extreme, pure quantum coherence. The walker spreads across every path simultaneously, interfering everywhere. Neither extreme is useful on its own. At intermediate settings the walker interferes *and* diffuses, and probability sculpting becomes possible. The equation has one dial, and that dial maps directly onto the γ/κ parameter from Chapter 8, the ratio of quantum coherence to environmental noise.

The adaptive measurement thesis adds a feedback loop: the outcome of each quantum measurement changes what gets measured next. The protein's current shape determines the quantum evolution. The quantum outcome changes the protein's shape. The new shape determines the next evolution. Each individual step is standard quantum mechanics. The feedback loop is standard control theory (Wiseman and Milburn, 2009). Nothing exotic is required.

There is a temptation in quantum biology to write down continuous-time equations where the measurement operator depends on the system's own state. This looks elegant but breaks a foundational guarantee of quantum mechanics called complete positivity. The math stops being physically valid. NFT does not require this shortcut. The actual mechanism is a discrete cycle: evolve the radical pair, record the outcome, update the protein conformation, repeat. Each step is a standard quantum operation. The full sequence is standard quantum feedback control. The formalism is well-defined, and the computational simulations implement exactly this cycle. The formal details are developed in [Malloy 2026].

### The Negative Conditional Entropy Wedge

Chapter 7 argued that quantum systems can carry a kind of information that classical systems provably cannot. The formal version of that claim comes down to a single measurable quantity. If entangled radical pairs in microtubules exhibit negative conditional entropy under physiological conditions, the navigator has access to resources that classical information theory forbids. The measurement is called spin state tomography, and it is within reach of current laboratory techniques. Nobody has done it yet.

### The Multi-Scale Synthesis

The full formalization needs to connect three scales of description. Each needs its own mathematics, and the scales need to communicate with each other.

Zoom in to a single page and you see one choice, one radical pair event, one quantum measurement with a definite outcome. The mathematics here is quantum mechanics, Hilbert space, measurement operators, back-action. Zoom out to the path through the book and you see a trajectory curving through a landscape of choices, some paths shorter than others, some more probable. The mathematics here is Riemannian geometry, conscious trajectories following shortest paths on curved surfaces defined by neural connectivity. Zoom out further, to the book itself. All paths, all endings, the rules governing which choices lead where, and you see the architecture. The mathematics here is category theory, the structural relationships between IIT, GNWT, and the quantum substrate as components of a single navigational system.

Phillips and Tsuchiya showed that all of IIT's axioms derive from a single mathematical structure called the universal mapping property. Category theory may be the natural language for consciousness, arrived at from the other direction.

### What Remains

NFT at present is more precise than a metaphor but less precise than a mathematical theory.

The discrete-time formulation is well-defined. Whether it can be compressed into a compact continuous-time representation while preserving complete positivity is a convenience question, not a physical one. The harder open problem is the multi-scale synthesis. Deriving Φ, broadcasting dynamics, and radical pair measurement from a single navigational principle would close the loop between the theory's three scales. That derivation has not been done.

The formalization horizon is visible. Whether it can be reached is the work ahead.
