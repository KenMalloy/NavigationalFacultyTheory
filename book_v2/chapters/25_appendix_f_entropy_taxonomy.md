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

An entropy-derived consciousness measure developed by Casali and colleagues (2013). PCI combines TMS stimulation with algorithmic complexity of the evoked EEG response. It measures not how complex the brain's spontaneous activity is, but how complex its *response to perturbation* is. A system at criticality should show maximal PCI; departures from criticality should reduce it. PCI reliably tracks consciousness level across wakefulness, sleep, anesthesia, and disorders of consciousness without requiring behavioral report.

### Conditional Entropy (Including Negative Quantum Conditional Entropy)

Classical conditional entropy, H(A|B) = H(A,B) − H(B), measures uncertainty remaining about system A after observing system B. It is always non-negative classically: knowing more never makes you more uncertain. Quantum conditional entropy breaks this rule. For entangled states, it can go negative — something classically forbidden. Negative conditional entropy is a genuine quantum-only resource, provably inaccessible to classical systems. The book invokes it as a theoretical ceiling that conscious systems, if quantum-coupled, might approach.

### Thermodynamic Entropy

The entropy of the second law. It defines the arrow of time and the gradient along which NFT claims consciousness navigates. When the book says "the entropy gradient" or "the entropic current," this is the notion in play. Consciousness, on NFT's account, does not reverse the current. It steers within it.

### How They Fit Together

The argument moves across these notions deliberately. Thermodynamic entropy provides the navigational gradient. Shannon, Tsallis, and Rényi provide the empirical measurement tools. PCI provides the clinical bridge. Trajectory entropy is what consciousness actually reduces. Negative conditional entropy marks the boundary between what classical and quantum systems can achieve.

---

