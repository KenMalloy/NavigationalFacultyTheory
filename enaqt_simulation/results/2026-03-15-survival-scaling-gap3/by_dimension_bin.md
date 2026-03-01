# Maze Scaling Confirmatory Summary

- Source CSV: `enaqt_simulation/results/2026-03-15-survival-scaling-gap3/combined.csv`
- Per-maze rows loaded: `90`
- Confirmatory groups: `9`
- Group columns: `maze_dim, latent_dim, bin_label`

## Confirmatory Table

| maze_dim | latent_dim | bin_label | n_mazes | normalized_adv_pct_mean | normalized_adv_pct_ci_low | normalized_adv_pct_ci_high | survival_lift_pct_mean | survival_lift_pct_ci_low | survival_lift_pct_ci_high | maze_quantum_win_rate | maze_quantum_win_ci_low | maze_quantum_win_ci_high | detour_ratio_mean | open_fraction_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 5 | easy | 10 | 14.3318 | -11.9991 | 40.6628 | 14.3318 | -11.9991 | 40.6628 | 0.7000 | 0.3968 | 0.8922 | 1.0200 | 0.7025 |
| 2 | 5 | hard | 10 | 1.5811 | -6.9533 | 10.1155 | 1.5811 | -6.9533 | 10.1155 | 0.5000 | 0.2366 | 0.7634 | 1.5200 | 0.7058 |
| 2 | 5 | medium | 10 | 12.9263 | -1.6248 | 27.4774 | 12.9263 | -1.6248 | 27.4774 | 0.6000 | 0.3127 | 0.8318 | 1.2400 | 0.7000 |
| 3 | 6 | easy | 10 | 5.0577 | -1.3027 | 11.4181 | 5.0577 | -1.3027 | 11.4181 | 0.4000 | 0.1682 | 0.6873 | 1.0083 | 0.6510 |
| 3 | 6 | hard | 10 | 7.8641 | 1.9054 | 13.8228 | 7.8641 | 1.9054 | 13.8228 | 0.7000 | 0.3968 | 0.8922 | 1.5083 | 0.5733 |
| 3 | 6 | medium | 10 | 4.3881 | -2.7047 | 11.4809 | 4.3881 | -2.7047 | 11.4809 | 0.5000 | 0.2366 | 0.7634 | 1.2250 | 0.6099 |
| 4 | 7 | easy | 10 | 4.9045 | -6.6220 | 16.4311 | 4.9045 | -6.6220 | 16.4311 | 0.6000 | 0.3127 | 0.8318 | 1.0500 | 0.4834 |
| 4 | 7 | hard | 10 | 1.7464 | -6.2620 | 9.7548 | 1.7464 | -6.2620 | 9.7548 | 0.5000 | 0.2366 | 0.7634 | 1.5200 | 0.4369 |
| 4 | 7 | medium | 10 | -1.2340 | -7.6139 | 5.1460 | -1.2340 | -7.6139 | 5.1460 | 0.4000 | 0.1682 | 0.6873 | 1.2200 | 0.4448 |

## Notes

- Unit of inference: maze.
- Headline effect: per-maze normalized advantage, then grouped across mazes.
- Maze win rate uses a Wilson interval.
- Mean intervals use normal-approximation SEM intervals with the chosen z value.
- Trial-level outcomes are intentionally not treated as independent confirmatory samples.
