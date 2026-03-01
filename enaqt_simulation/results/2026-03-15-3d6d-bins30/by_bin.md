# Maze Scaling Confirmatory Summary

- Source CSV: `enaqt_simulation/results/2026-03-15-3d6d-bins30/3d6d_bins30.csv`
- Per-maze rows loaded: `90`
- Confirmatory groups: `3`
- Group columns: `maze_dim, latent_dim, bin_label`

## Confirmatory Table

| maze_dim | latent_dim | bin_label | n_mazes | normalized_adv_pct_mean | normalized_adv_pct_ci_low | normalized_adv_pct_ci_high | survival_lift_pct_mean | survival_lift_pct_ci_low | survival_lift_pct_ci_high | maze_quantum_win_rate | maze_quantum_win_ci_low | maze_quantum_win_ci_high | detour_ratio_mean | open_fraction_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 6 | easy | 30 | 2.6795 | -2.2847 | 7.6437 | 2.6795 | -2.2847 | 7.6437 | 0.4000 | 0.2459 | 0.5768 | 1.0111 | 0.6445 |
| 3 | 6 | hard | 30 | 3.8472 | -0.0624 | 7.7568 | 3.8472 | -0.0624 | 7.7568 | 0.6333 | 0.4551 | 0.7813 | 1.5056 | 0.5809 |
| 3 | 6 | medium | 30 | 3.4347 | -0.4445 | 7.3139 | 3.4347 | -0.4445 | 7.3139 | 0.5667 | 0.3920 | 0.7262 | 1.2250 | 0.5960 |

## Notes

- Unit of inference: maze.
- Headline effect: per-maze normalized advantage, then grouped across mazes.
- Maze win rate uses a Wilson interval.
- Mean intervals use normal-approximation SEM intervals with the chosen z value.
- Trial-level outcomes are intentionally not treated as independent confirmatory samples.
