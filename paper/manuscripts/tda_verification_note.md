# TDA Pipeline Verification Note

Date: 2026-03-16

## Purpose

Verify reproducibility of the propofol TDA temporal ordering results
(04_temporal_ordering.py) after reinstalling dependencies in a fresh
Python 3.14 virtual environment.

## Procedure

1. Recreated the project venv (the previous one had a broken interpreter
   path pointing to a moved directory).
2. Installed pandas 3.0.1, numpy 2.4.3, scipy 1.17.1, matplotlib 3.10.8.
3. Ran 04_temporal_ordering.py against the existing all_subjects_metrics.csv
   (12,518 epochs from 21 subjects).

## Results

The script completed without errors. Output values match the prior results
exactly:

| Metric     | median_diff | p        | nft_supported |
|------------|-------------|----------|---------------|
| lempel_ziv | -57.0       | 0.9579   | False         |
| wpli_alpha | -59.5       | 0.9984   | False         |

These match the expected values. The negative median differences indicate
that classical metrics changed before topological metrics, opposite to the
NFT prediction. Neither comparison has a confidence interval entirely
above zero, so nft_supported = False for both.

## Issues

- The original .venv had a broken shebang (pip referenced a moved path at
  /Users/kennethmalloy/claude/.venv). Resolved by recreating the venv with
  --clear.
- No other issues. All dependencies installed cleanly on Python 3.14.

## Conclusion

Results are reproducible. The propofol TDA negative result is confirmed.
