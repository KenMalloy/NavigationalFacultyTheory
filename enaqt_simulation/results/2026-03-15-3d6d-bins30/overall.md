# Maze Scaling Confirmatory Summary

- Source CSV: `enaqt_simulation/results/2026-03-15-3d6d-bins30/3d6d_bins30.csv`
- Per-maze rows loaded: `90`
- Confirmatory groups: `1`
- Group columns: `maze_dim, latent_dim`

## Confirmatory Table

| maze_dim | latent_dim | n_mazes | normalized_adv_pct_mean | normalized_adv_pct_ci_low | normalized_adv_pct_ci_high | survival_lift_pct_mean | survival_lift_pct_ci_low | survival_lift_pct_ci_high | maze_quantum_win_rate | maze_quantum_win_ci_low | maze_quantum_win_ci_high | detour_ratio_mean | open_fraction_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 6 | 90 | 3.3205 | 0.8748 | 5.7662 | 3.3205 | 0.8748 | 5.7662 | 0.5333 | 0.4310 | 0.6329 | 1.2472 | 0.6071 |

## Notes

- Unit of inference: maze.
- Headline effect: per-maze normalized advantage, then grouped across mazes.
- Maze win rate uses a Wilson interval.
- Mean intervals use normal-approximation SEM intervals with the chosen z value.
- Trial-level outcomes are intentionally not treated as independent confirmatory samples.
