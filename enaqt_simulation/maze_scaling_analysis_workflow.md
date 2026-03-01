# Maze Scaling Analysis Workflow

This note is for the export and review side of the maze benchmark.

## Confirmatory outputs

Use one CSV row per maze/spec as the only confirmatory input table.

Required confirmatory summaries:

- `n_mazes` per bin/spec
- mean normalized advantage across mazes
- interval on normalized advantage
- maze win rate, with a proportion interval
- geometry sanity summaries: shortest path, detour ratio, open fraction

Confirmatory reporting rules:

- Treat the maze as the unit of inference.
- Do not pool paired trials as if they were independent mazes.
- Keep bin/spec definitions fixed before the run you intend to cite.
- Publish the per-maze CSV alongside any derived summary table.

## Exploratory outputs

Exploratory outputs are useful, but they should be labeled as such.

Examples:

- example mazes
- example trajectories
- post hoc slices by detour ratio or open fraction
- alternative normalizations
- correlation/regression analyses added after looking at the results

## Recommended artifact split

- canonical per-maze export CSV
- confirmatory summary CSV derived only from the per-maze export
- optional markdown summary for reviewers
- exploratory plots and notes in a separate folder or section
