# Maze Scaling Confirmatory Summary

- Source CSV: `enaqt_simulation/results/2026-03-15-survival-scaling-gap3/combined.csv`
- Per-maze rows loaded: `90`
- Confirmatory groups: `3`
- Group columns: `maze_dim, latent_dim`

## Confirmatory Table

| maze_dim | latent_dim | n_mazes | normalized_adv_pct_mean | normalized_adv_pct_ci_low | normalized_adv_pct_ci_high | survival_lift_pct_mean | survival_lift_pct_ci_low | survival_lift_pct_ci_high | maze_quantum_win_rate | maze_quantum_win_ci_low | maze_quantum_win_ci_high | detour_ratio_mean | open_fraction_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 5 | 30 | 9.6131 | -0.6571 | 19.8833 | 9.6131 | -0.6571 | 19.8833 | 0.6000 | 0.4232 | 0.7541 | 1.2600 | 0.7028 |
| 3 | 6 | 30 | 5.7700 | 2.1145 | 9.4255 | 5.7700 | 2.1145 | 9.4255 | 0.5333 | 0.3614 | 0.6977 | 1.2472 | 0.6114 |
| 4 | 7 | 30 | 1.8057 | -3.2363 | 6.8477 | 1.8057 | -3.2363 | 6.8477 | 0.5000 | 0.3315 | 0.6685 | 1.2633 | 0.4550 |

## Notes

- Unit of inference: maze.
- Headline effect: per-maze normalized advantage, then grouped across mazes.
- Maze win rate uses a Wilson interval.
- Mean intervals use normal-approximation SEM intervals with the chosen z value.
- Trial-level outcomes are intentionally not treated as independent confirmatory samples.
