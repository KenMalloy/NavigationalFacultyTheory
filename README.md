# The Navigational Faculty: A New Theory of Consciousness

**Kenneth Malloy** | Draft v2.1 — March 2026

---

Every morning you wake up and something happens that no theory in science can explain. The lights come on. Not the lights in your room, the lights of experience. The world appears with texture and weight and presence, and there is a *you* doing the appearing-to. This book is about what that is.

Navigational Faculty Theory makes a single claim in three layers. The outermost layer says what consciousness *does*: it navigates. The middle layer says *how*: through a quantum mechanism in which living systems reshape the odds of their own futures. The innermost layer says what consciousness *navigates through*: a physically real possibility space. Each layer is independently testable. Each can fail without killing the others.

This book contains two significant negative results reported in full: a simulation that ruled out the original proposed quantum mechanism, and an empirical reanalysis that failed to support one of the theory's predictions. The negative results make the theory stronger, because they show it is making contact with reality rather than insulating itself from it.

---

## Table of Contents

### [Full Book](book_draft_v2.md) | Individual Chapters:

| # | Chapter | Part |
|---|---------|------|
| — | [Preface & Glossary](book_v2/chapters/00_preface.md) | Front Matter |
| 1 | [The Hard Problem](book_v2/chapters/01_hard_problem.md) | I: The Problem and the Method |
| 2 | [Why It's Structurally Hard](book_v2/chapters/02_structurally_hard.md) | I |
| 3 | [Testability as Method](book_v2/chapters/03_testability.md) | I |
| 4 | [Consciousness as Navigation](book_v2/chapters/04_navigation.md) | II: Level A — Navigation as Function |
| 5 | [The Entropic Current](book_v2/chapters/05_entropic_current.md) | II |
| 6 | [The Evolutionary Case](book_v2/chapters/06_evolutionary_case.md) | II |
| 7 | [The Categorical Difference](book_v2/chapters/07_categorical_difference.md) | III: Level B — Quantum Probability Sculpting |
| 8 | [The Honest Path to the Mechanism](book_v2/chapters/08_honest_path.md) | III |
| 9 | [How Sculpting Works](book_v2/chapters/09_how_sculpting_works.md) | III |
| 10 | [The Navigation Benchmark](book_v2/chapters/10_navigation_proof.md) | III |
| 11 | [Zeno, Anti-Zeno, and the Dynamics of Attention](book_v2/chapters/11_zeno.md) | IV: Level B — Deeper Consequences |
| 12 | [Qualia as Measurement Back-Action](book_v2/chapters/12_qualia.md) | IV |
| 13 | [Binding Through Topology](book_v2/chapters/13_binding_topology.md) | IV |
| 14 | [What Possibility Space Is](book_v2/chapters/14_possibility_space.md) | V: Level C — The Ontology of Possibility |
| 15 | [The Experimental Program](book_v2/chapters/15_experimental_program.md) | VI: Testing and Implications |
| 16 | [Implications](book_v2/chapters/16_implications.md) | VI |
| 17 | [The Formalization Horizon](book_v2/chapters/17_formalization.md) | VI |
| — | [Epilogue: The Navigator](book_v2/chapters/18_epilogue.md) | — |
| — | [Appendices](book_v2/chapters/19_appendices.md) | — |

---

## Repository Structure

```
enaqt_simulation/          Simulation code (all results reported in the book)
├── core.py                    ENAQT framework (phenomenological + Bloch-Redfield)
├── phase1_bias.py             Quantum bias measurement
├── phase2_transport.py        Transport efficiency analysis
├── phase2_bloch_redfield.py   Physically-derived quantum dynamics
├── phase3_evolve.py           Evolutionary optimization over geometry
├── quantum_vs_classical.py    Quantum vs classical comparison
├── spin_coherence.py          Radical pair spin dynamics (the mechanism that worked)
├── criticality_amplification.py   Criticality amplification (Ch. 9)
├── measurement_basis_selection.py  Adaptive measurement basis selection
├── directed_navigation.py     Directed navigation benchmark
├── maze_navigator.py          3D maze navigation framework (Ch. 10)
├── maze_scaling_sweep.py      90-maze scaling analysis (Ch. 10)
├── transduction_chain.py      Full transduction chain calculation (Ch. 9)
├── conformational_tunneling.py    Conformational tunneling (ruled out)
└── trajectory_analysis.py     Trajectory divergence analysis

nft-tda-reanalysis/        Topological Data Analysis pipeline (the negative result)
├── 01_download.py             Dataset acquisition (OpenNeuro DS005620)
├── 02_preprocess.py           EEG preprocessing
├── 03_compute_metrics.py      Persistent homology + classical metrics
├── 04_temporal_ordering.py    Temporal ordering analysis
└── run_pipeline.py            Full pipeline runner

simulations/               Anti-Zeno spectral analysis
results/                   EEG metric outputs (21 subjects, propofol sedation)
figures/                   TDA reanalysis figures
research/                  Deep research reports (literature reviews)
paper/                     Earlier drafts (v1 book draft, original paper draft)
docs/plans/                Design documents and work plans
```

## Key Results

| Claim | Result | Chapter |
|-------|--------|---------|
| Excitonic ENAQT in microtubules | **Ruled out.** +0.18% quantum advantage at 310K. | 8 |
| Radical pair spin coherence | **Viable.** 12.7% yield difference, 1.48 μs coherence at 310K. | 8 |
| Criticality amplifies quantum bias | **Confirmed.** 0.2% bias → 10.2% network effect at σ=1.0. | 9 |
| Transduction chain viability | **Conditionally viable.** 10x below noise at baseline ROS, viable at elevated ROS. | 9 |
| Quantum navigational advantage | **Modest but systematic.** +3.3% across 90 mazes, CI excludes zero. | 10 |
| Topological disruption order | **Not supported.** Classical metrics declined first. | 13 |

## Running the Simulations

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install numpy scipy

# Run any simulation (examples)
python enaqt_simulation/criticality_amplification.py
python enaqt_simulation/spin_coherence.py
python enaqt_simulation/maze_scaling_sweep.py
```

The TDA reanalysis has its own environment and requirements. See [nft-tda-reanalysis/README.md](nft-tda-reanalysis/README.md).

## Acknowledgments

This work stands on the shoulders of extraordinary researchers across many disciplines.

**Consciousness Studies & Philosophy of Mind:** Giulio Tononi (IIT), Bernard Baars (Global Workspace Theory), Stanislas Dehaene & Jean-Pierre Changeux (GNWT), David Chalmers (the hard problem), Stuart Hameroff & Roger Penrose (Orch OR), Robin Carhart-Harris (entropic brain hypothesis), Adam Safron (IWMT), Karl Friston (Free Energy Principle), Jonathan Edwards (N-Frame), Paul Skokowski (qualia as detector alteration), Donald Hoffman (interface theory), Henry Stapp (observer effects), Kelvin McQueen (consciousness-collapse), Erik Hoel & Max Kleiner (structural constraints), Adrien Doerig, Arno Schurger & Michael Herzog (hard criteria).

**Quantum Biology:** Nathan S. Babcock et al. (tryptophan superradiance), Aarat P. Kalra et al. (exciton diffusion in microtubules), Travis J. A. Craddock et al. (structure-based energy transfer, anesthetic binding), Saif Khan et al. (microtubule-stabilizing drugs), Hadi Zadeh-Haghighi et al. (radical pair spin coherence in biological systems), Timothy Oblinski et al. (excitation energy transfer).

**Quantum Physics & Foundations:** Max Tegmark (decoherence challenge), Martin B. Plenio & Susana F. Huelga (ENAQT), Masoud Mohseni et al. (environment-assisted quantum walks), James D. Whitfield, Cesar A. Rodriguez-Rosario & Alan Aspuru-Guzik (quantum stochastic walks), B. Misra & E.C.G. Sudarshan (quantum Zeno effect), A.G. Kofman & G. Kurizki (anti-Zeno effect), Wojciech Zurek (quantum Darwinism), Christopher Fuchs (QBism), Yakir Aharonov et al. (weak measurement).

**Information Theory & Complexity:** Andrey Kolmogorov, Gregory Chaitin, Charles Bennett, Constantino Tsallis (non-extensive entropy), Craig DeLancey (Kolmogorov complexity and phenomenal experience), Hector Zenil (Algorithmic Information Dynamics).

**Cognitive Science:** Jerome Busemeyer & Peter Bruza (quantum cognition), Emmanuel Pothos & Jerome Busemeyer (quantum probability models), Douglas Hofstadter (strange loops), Andrei Khrennikov (contextuality in cognition).

**Neuroscience:** Melanie Schartner et al. (EEG complexity), Andrea Casali et al. (PCI), Andrea Luppi et al. (fMRI entropy), Laurent Naccache et al. (COGITATE), Kevin Hengen et al. (neural criticality), Rudiger Thul et al. (permutation entropy), Andres Canales-Johnson et al. (information-theoretic consciousness measurement).

**Topology & Structural Biology:** Michael Reimann et al. (Blue Brain Project, simplicial complexes), Dominique Santoro et al. (higher-order neural indicators), Steven Phillips & Naotsugu Tsuchiya (category theory and consciousness axioms).

**Evolutionary Biology & Non-Neural Cognition:** Tetsu Nakagaki et al. (slime mold maze-solving), Atsushi Tero et al. (biological transport networks), Taiko Fukasawa et al. (mycelial spatial memory), Paco Calvo et al. (plant cognition).

**Thermodynamics & Self-Organization:** Ilya Prigogine (dissipative structures), Jeremy England (driven systems and entropy dissipation), Gualtiero Chen & Robert Sanders (CER model), Dharshana Jha (entropy-driven awareness), Meir Hemmo & Orly Shenker (psychological arrow of time).

To every researcher listed here, and the many collaborators, students, and teams behind each citation: thank you. Your work across disciplines is what makes an integrative theory like NFT even conceivable.

*-- Kenneth Malloy*

---

*A theory that tells you how to kill it is doing science. A theory that cannot be killed is doing something else.*
