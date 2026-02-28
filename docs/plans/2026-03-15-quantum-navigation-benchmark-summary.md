# Quantum Navigation Benchmark Summary

## Why this was still scientific

The working principle was:

- It is acceptable to search for stronger examples of quantum advantage.
- It is not acceptable to change the benchmark in ways that only make the quantum controller look good.

The changes we made were aimed at keeping the search scientific rather than cherry-picked:

- We introduced real classical baselines, including a full-map shortest-path planner and local map-free heuristics.
- We compared `Quantum+Adaptive` against a matched `Classical+Adaptive` controller, where both sides were evolved.
- We averaged across multiple mazes instead of relying on one lucky instance.
- We used a shared training budget (`--train-evals`) so higher-dimensional controllers did not silently receive more optimization.
- We preserved negative and mixed results instead of filtering them out.

The honest framing that emerged is:

- The shortest-path planner remains the classical upper bound and solves every maze benchmark.
- The interesting question is not "does quantum beat classical planning?"
- The interesting question is "when does a learned quantum-adaptive controller outperform a matched learned classical-adaptive controller?"

## What we changed

### 1. Added real classical baselines to the original maze benchmark

In [maze_navigator.py](/Users/kennethmalloy/nft/enaqt_simulation/maze_navigator.py):

- Added `ShortestPathPlanner`
- Added `RightWallFollower`
- Added `LeftWallFollower`
- Added independently re-optimized learned controls:
  - `FixedBasis+Reoptimized`
  - `Classical+Reoptimized`

This changed the interpretation of the original maze claim from "quantum solves mazes better than classical" to "the learned quantum controller can beat some matched learned controls or local heuristics on some mazes, but not the best classical planner."

### 2. Built a fairer scaling benchmark

In [maze_scaling_sweep.py](/Users/kennethmalloy/nft/enaqt_simulation/maze_scaling_sweep.py):

- Added a matched `Classical+Adaptive` baseline with a learned state-dependent stochastic gate.
- Added averaging over multiple mazes per spec.
- Added parameter-budget normalization through `--train-evals`.
- Added geometry overrides so maze size, barrier count, and gap count can be tuned systematically.
- Added latent-dimension sweeps through:
  - `--maze-dims`
  - `--latent-dims`
  - `--latent-offsets`

## Results observed

### A. Original 2D maze benchmark with real classical baselines

Representative reality check:

- On the `hard` maze, `Quantum+Evolved` did not beat competent classical planning.
- Re-optimized classical learned controls largely erased the earlier quantum gap.
- On the `fourway` maze, the quantum controller could still beat some re-optimized learned controls, but not the shortest-path planner.

Takeaway:

- The original maze result is best treated as proof-of-principle, not as a broad superiority claim.

### B. Fair default scaling sweep: `2D/6D`, `3D/7D`, `4D/8D`

Direct local runs on the current script:

#### `--train-evals 240 --n-seeds-ga 2 --n-runs 10 --mazes-per-spec 2`

- `2D/6D`: quantum advantage `+0.20 +/- 2.60`
- `3D/7D`: quantum advantage `+4.80 +/- 3.70`
- `4D/8D`: quantum advantage `-0.50 +/- 0.90`

#### `--train-evals 360 --n-seeds-ga 2 --n-runs 15 --mazes-per-spec 2`

- `2D/6D`: quantum advantage `-0.13 +/- 1.47`
- `3D/7D`: quantum advantage `+5.13 +/- 3.07`
- `4D/8D`: quantum advantage `+0.73 +/- 0.87`

#### `--train-evals 500 --n-seeds-ga 3 --n-runs 10 --mazes-per-spec 2`

- `2D/6D`: quantum advantage `+1.80 +/- 2.20`
- `3D/7D`: quantum advantage `+5.35 +/- 2.25`
- `4D/8D`: quantum advantage `+1.30 +/- 1.30`

Takeaway:

- `2D/6D` was basically a wash.
- `3D/7D` showed the clearest moderate, repeatable positive signal.
- `4D/8D` was weak and inconsistent.

This was suggestive of an emerging middle-dimensional advantage, but not a clean monotonic scaling law.

### C. Latent-gap sweeps on the smaller default 3D family

We then held maze dimension fixed and varied latent dimension directly.

For `3D` at higher budget:

- `3D/3D`: quantum advantage `+5.67 +/- 2.98`
- `3D/5D`: quantum advantage `+3.51 +/- 1.78`
- `3D/7D`: quantum advantage `+5.96 +/- 0.89`
- `3D/9D`: quantum advantage `+1.76 +/- 1.71`

Takeaway:

- `+4` was not a theorem.
- More latent dimensions did not automatically help.
- The effect looked non-monotonic and suggested a broad sweet spot rather than "bigger is better."

### D. Search for more meaningful 3D geometries

We scanned 3D maze geometries by varying:

- `side`
- `barriers`
- `gaps_per_barrier`

Goal:

- move away from families with detour ratio near `1.00x`
- keep the benchmark solvable
- avoid making every controller fail uniformly

Promising harder family found:

- `side=9`
- `barriers=6`
- `gaps=2`
- average detour roughly `1.39x +/- 0.04`

This was better than the earlier near-trivial `1.00x` families.

### E. Larger 3D pilot on the harder family: `side=9, barriers=6, gaps=2`

Pilot command family:

- `--maze-dims 3 --latent-dims 3,5,7,9 --side-override 9 --barriers-override 6 --gaps-override 2 --train-evals 240 --n-seeds-ga 2 --n-runs 10 --mazes-per-spec 3`

Observed:

- `3D/3D`: quantum advantage `-0.87 +/- 1.05`
- `3D/5D`: quantum advantage `+5.00 +/- 3.60`
- `3D/7D`: quantum advantage `+4.20 +/- 5.28`
- `3D/9D`: quantum advantage `-0.13 +/- 5.08`

Takeaway:

- On the harder 3D family, the positive signal concentrated in the middle latent range.
- The easy headline was no longer "7D is best."
- The better headline became "moderate latent gaps seem better than zero gap or very large gap."

### F. Focused follow-up on the harder 3D family

Focused command:

```bash
./.venv/bin/python enaqt_simulation/maze_scaling_sweep.py \
  --maze-dims 3 \
  --latent-dims 4,5,6,7 \
  --side-override 9 \
  --barriers-override 6 \
  --gaps-override 2 \
  --train-evals 500 \
  --n-seeds-ga 3 \
  --n-runs 15 \
  --mazes-per-spec 5
```

Observed:

- `3D/4D`: quantum advantage `+3.95 +/- 6.27`
- `3D/5D`: quantum advantage `+6.64 +/- 5.42`
- `3D/6D`: quantum advantage `+7.33 +/- 5.77`
- `3D/7D`: quantum advantage `+2.32 +/- 4.36`

Takeaway:

- The best current regime is not "highest latent dimension."
- The strongest current candidates are `3D/5D` and `3D/6D`.
- `3D/7D` is still positive, but no longer looks like the clear optimum on the harder family.

## Current scientific interpretation

At this point the best honest interpretation is:

- The benchmark work became more scientific, not less, as we searched for stronger examples.
- That is because the search was carried out over benchmark families with matched baselines, shared budgets, and retained negative findings.
- The strongest current result is not a universal quantum advantage.
- The strongest current result is a regime claim:
  - on some harder 3D maze families, a middle latent gap appears to help the learned quantum-adaptive controller outperform a matched learned classical-adaptive controller.

What we can say:

- There appears to be a "sweet spot" in latent dimensionality.
- On larger 3D mazes, that sweet spot currently looks closer to `3D/5D` or `3D/6D` than to `3D/7D`.

What we cannot say:

- We cannot claim monotonic scaling with dimension.
- We cannot claim quantum superiority over classical planning in general.
- We cannot claim that higher latent dimension always helps.

## Most important limitations

- The shortest-path planner still solves every benchmark.
- The main comparison is learned quantum-adaptive vs learned classical-adaptive, not quantum vs all classical methods.
- The current score emphasizes final distance and goal rate more than trajectory quality.
- Since the NFT claim also cares about path and process, future versions should incorporate a stronger path-sensitive objective or reporting layer.

## Best current headline

If this were turned into manuscript language right now, the strongest defensible version would be:

> We systematically searched benchmark families rather than a single hand-picked maze. Under matched training budgets and matched adaptive classical baselines, the clearest signal emerged not from maximal latent dimensionality, but from a middle-gap regime on harder 3D mazes, where `3D/5D` to `3D/6D` controllers currently outperform the learned classical-adaptive baseline most consistently.

## Recommended next step

The most useful next confirmation experiment is:

```bash
./.venv/bin/python enaqt_simulation/maze_scaling_sweep.py \
  --maze-dims 3 \
  --latent-dims 5,6 \
  --side-override 9 \
  --barriers-override 6 \
  --gaps-override 2 \
  --train-evals 700 \
  --n-seeds-ga 3 \
  --n-runs 20 \
  --mazes-per-spec 10
```

That would test whether the apparent `3D/5D` versus `3D/6D` sweet spot holds up under more averaging on the harder 3D family.
