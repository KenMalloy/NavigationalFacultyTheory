# Evidence Audit Implementation Plan

**Date:** 2026-03-16
**Goal:** Apply all evidence audit feedback across 7 manuscripts + independently verify all simulation outputs

## Architecture: 8 Parallel Agents

### Agents 1-7: One per manuscript (editorial + citations)

Each agent reads its manuscript + the relevant section of `paper/manuscripts/evidence_audit.md` and applies:
- Claim softening per audit's "Revision needed" column
- Red-flag phrase replacements per audit's list
- Missing primary citation additions per audit's bibliography cleanup
- Structural fixes (assumptions tables, limitations paragraphs, retitling)

| Agent | Manuscript | Audit Rank | Key Focus |
|-------|-----------|------------|-----------|
| 1 | 01_trajectory_entropy_unification | 6 | Scope down, add primary citations, recast as proposal |
| 2 | 02_enaqt_negative_result | 3 | Narrow to "baseline model," add limitations paragraph |
| 3 | 03_quantum_navigation_benchmark | 1 | Quote fairness rules, add planner appendix, narrow claims |
| 4 | 04_radical_pair_tubulin_feasibility | 4 | Assumptions table, "parameterized feasibility model" language |
| 5 | 05_discriminative_program | 5 | Concrete framework, link to exact result files |
| 6 | 06_propofol_tda_negative_result | 2 | Proxy limitation in abstract, dataset DOI |
| 7 | 07_qualia_back_action | 7 | Conjectural framing, non-claim near front |

### Agent 8: Simulation Verifier

Independently reruns all key simulations and compares outputs to numbers claimed in manuscripts:
- `spin_coherence.py` → 12.7% yield difference, 1.48 μs coherence
- `criticality_amplification.py` → 0.2% bias → 10.2% effect at σ=1.0
- `phase2_transport.py` → 0.18% quantum advantage
- `transduction_chain.py` → ~10 events/5ms, ~10μV signal
- `branching_navigation_sim.py` → 86.985 → 91.663 → 98.437
- Flag: TDA pipeline needs pandas (cannot rerun)
- Flag: maze_scaling_sweep.py (verify subset, full 90-maze run is long)

## Success Criteria

1. Every claim in every manuscript is graded and qualified per the audit
2. Every red-flag phrase is replaced with its safer alternative
3. Every missing primary citation is added
4. Simulation outputs independently verified against manuscript claims
5. Any discrepancies surfaced immediately
