"""
Analyze canonical per-maze maze-scaling exports.

This helper is intentionally downstream-only: it consumes a CSV with one row
per maze/spec and produces confirmatory summaries suitable for reviewer-facing
 reporting.

Expected canonical schema
=========================

Required columns
----------------
- One maze identifier column:
  - `maze_id`, or
  - `maze_seed`
- Spec identifiers:
  - `maze_dim`
  - `latent_dim`
- Geometry sanity columns:
  - `shortest_path` (alias accepted: `shortest`)
  - `detour_ratio`
  - `open_fraction`
- Confirmatory outcome:
  - `paired_norm_adv_pct_mean`
    Aliases accepted: `norm_advantage`, `norm_advantage_mean`,
    `paired_normalized_advantage_pct_mean`,
    `paired.normalized_advantage_pct_mean`
- At least one maze-win source:
  - `maze_quantum_win`, or
  - `paired_raw_adv_mean`
    Aliases accepted: `advantage`, `raw_advantage_mean`,
    `paired_raw_advantage_mean`, `paired.raw_advantage_mean`

Recommended columns
-------------------
- `run_id`
- `spec_mode`
- `spec_id`
- `bin_id`
- `bin_label`
- `side`
- `barriers`
- `gaps_per_barrier`
- `effective_train_evals`
- `n_runs_eval` or `paired_n_trials`
- `quantum_mean_dist`
- `classical_mean_dist`
- `planner_mean_dist`
- `paired_quantum_win_rate`

Confirmatory unit of inference
------------------------------
This script treats the maze as the unit of inference. Trial-level counts can
be displayed if present, but the headline summaries are always aggregated over
per-maze rows, never over paired trials.

Derived survival metric
-----------------------
When controller mean distances are present, this helper derives:

- `quantum_survival_pct = 100 * (1 - quantum_mean_dist / shortest_path)`
- `classical_survival_pct = 100 * (1 - classical_mean_dist / shortest_path)`
- `survival_lift_pct = quantum_survival_pct - classical_survival_pct`

This treats "survival" as fraction of the shortest-path distance recovered.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


ALIASES: dict[str, tuple[str, ...]] = {
    "run_id": ("run_id",),
    "spec_mode": ("spec_mode",),
    "spec_id": ("spec_id",),
    "bin_id": ("bin_id",),
    "bin_label": ("bin_label",),
    "maze_id": ("maze_id",),
    "maze_seed": ("maze_seed",),
    "maze_dim": ("maze_dim",),
    "latent_dim": ("latent_dim",),
    "latent_gap": ("latent_gap",),
    "side": ("side",),
    "barriers": ("barriers",),
    "gaps_per_barrier": ("gaps_per_barrier",),
    "effective_train_evals": ("effective_train_evals",),
    "n_runs_eval": ("n_runs_eval", "paired_n_trials", "n_pairs"),
    "shortest_path": ("shortest_path", "shortest"),
    "detour_ratio": ("detour_ratio",),
    "open_fraction": ("open_fraction",),
    "paired_norm_adv_pct_mean": (
        "paired_norm_adv_pct_mean",
        "norm_advantage",
        "norm_advantage_mean",
        "paired_normalized_advantage_pct_mean",
        "paired.normalized_advantage_pct_mean",
    ),
    "paired_raw_adv_mean": (
        "paired_raw_adv_mean",
        "advantage",
        "raw_advantage_mean",
        "paired_raw_advantage_mean",
        "paired.raw_advantage_mean",
    ),
    "maze_quantum_win": ("maze_quantum_win", "quantum_wins", "quantum_win"),
    "quantum_mean_dist": ("quantum_mean_dist", "quantum.mean_dist"),
    "classical_mean_dist": ("classical_mean_dist", "classical.mean_dist"),
    "planner_mean_dist": ("planner_mean_dist", "planner.mean_dist"),
    "paired_quantum_win_rate": (
        "paired_quantum_win_rate",
        "trial_quantum_win_rate",
        "trial_quantum_win_rate_mean",
        "paired.quantum_win_rate",
    ),
}

REQUIRED_CANONICAL = (
    "maze_dim",
    "latent_dim",
    "shortest_path",
    "detour_ratio",
    "open_fraction",
    "paired_norm_adv_pct_mean",
)

OPTIONAL_NUMERIC = (
    "effective_train_evals",
    "n_runs_eval",
    "paired_raw_adv_mean",
    "quantum_mean_dist",
    "classical_mean_dist",
    "planner_mean_dist",
    "paired_quantum_win_rate",
)


def compute_survival_pct(shortest_path: float | None, mean_dist: float | None) -> float | None:
    if shortest_path is None or mean_dist is None or shortest_path <= 0:
        return None
    return 100.0 * (1.0 - (mean_dist / shortest_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path, help="Canonical per-maze export CSV")
    parser.add_argument(
        "--group-by",
        type=str,
        default="auto",
        help="Comma-separated canonical group columns, or 'auto'.",
    )
    parser.add_argument(
        "--summary-csv-out",
        type=Path,
        default=None,
        help="Optional path for confirmatory summary CSV.",
    )
    parser.add_argument(
        "--summary-md-out",
        type=Path,
        default=None,
        help="Optional path for markdown report.",
    )
    parser.add_argument(
        "--ci-z",
        type=float,
        default=1.96,
        help="Z value for normal-approximation mean intervals. Default: 1.96.",
    )
    return parser.parse_args()


def parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} contains no data rows")
    return rows


def resolve_aliases(headers: Iterable[str]) -> dict[str, str]:
    header_set = set(headers)
    mapping: dict[str, str] = {}
    for canonical, names in ALIASES.items():
        for name in names:
            if name in header_set:
                mapping[canonical] = name
                break
    return mapping


def require_schema(alias_map: dict[str, str]) -> None:
    missing = [name for name in REQUIRED_CANONICAL if name not in alias_map]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if "maze_id" not in alias_map and "maze_seed" not in alias_map:
        raise ValueError("Need either maze_id or maze_seed to validate one row per maze")
    if "maze_quantum_win" not in alias_map and "paired_raw_adv_mean" not in alias_map:
        raise ValueError(
            "Need either maze_quantum_win or paired_raw_adv_mean to summarize maze win rate"
        )


def parse_float(raw: str, column: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Could not parse {column}={raw!r} as float") from exc


def parse_int(raw: str, column: str) -> int:
    try:
        return int(float(raw))
    except ValueError as exc:
        raise ValueError(f"Could not parse {column}={raw!r} as int") from exc


def get_text(row: dict[str, str], alias_map: dict[str, str], canonical: str) -> str | None:
    source = alias_map.get(canonical)
    if source is None:
        return None
    raw = row.get(source, "")
    return raw if raw != "" else None


def get_float(row: dict[str, str], alias_map: dict[str, str], canonical: str) -> float | None:
    raw = get_text(row, alias_map, canonical)
    if raw is None:
        return None
    return parse_float(raw, canonical)


def get_int(row: dict[str, str], alias_map: dict[str, str], canonical: str) -> int | None:
    raw = get_text(row, alias_map, canonical)
    if raw is None:
        return None
    return parse_int(raw, canonical)


def canonicalize_rows(rows: list[dict[str, str]], alias_map: dict[str, str]) -> list[dict[str, object]]:
    canonical_rows: list[dict[str, object]] = []
    for idx, row in enumerate(rows, start=1):
        maze_dim = get_int(row, alias_map, "maze_dim")
        latent_dim = get_int(row, alias_map, "latent_dim")
        if maze_dim is None or latent_dim is None:
            raise ValueError(f"Row {idx} is missing maze_dim/latent_dim")

        latent_gap = get_int(row, alias_map, "latent_gap")
        if latent_gap is None:
            latent_gap = latent_dim - maze_dim

        paired_raw_adv_mean = get_float(row, alias_map, "paired_raw_adv_mean")
        maze_quantum_win = get_int(row, alias_map, "maze_quantum_win")
        if maze_quantum_win is None:
            maze_quantum_win = 1 if paired_raw_adv_mean is not None and paired_raw_adv_mean > 0 else 0

        canonical = {
            "run_id": get_text(row, alias_map, "run_id"),
            "spec_mode": get_text(row, alias_map, "spec_mode"),
            "spec_id": get_text(row, alias_map, "spec_id"),
            "bin_id": get_text(row, alias_map, "bin_id"),
            "bin_label": get_text(row, alias_map, "bin_label"),
            "maze_id": get_text(row, alias_map, "maze_id") or get_text(row, alias_map, "maze_seed"),
            "maze_seed": get_text(row, alias_map, "maze_seed"),
            "maze_dim": maze_dim,
            "latent_dim": latent_dim,
            "latent_gap": latent_gap,
            "side": get_int(row, alias_map, "side"),
            "barriers": get_int(row, alias_map, "barriers"),
            "gaps_per_barrier": get_int(row, alias_map, "gaps_per_barrier"),
            "effective_train_evals": get_float(row, alias_map, "effective_train_evals"),
            "n_runs_eval": get_float(row, alias_map, "n_runs_eval"),
            "shortest_path": get_float(row, alias_map, "shortest_path"),
            "detour_ratio": get_float(row, alias_map, "detour_ratio"),
            "open_fraction": get_float(row, alias_map, "open_fraction"),
            "paired_norm_adv_pct_mean": get_float(row, alias_map, "paired_norm_adv_pct_mean"),
            "paired_raw_adv_mean": paired_raw_adv_mean,
            "maze_quantum_win": maze_quantum_win,
            "quantum_mean_dist": get_float(row, alias_map, "quantum_mean_dist"),
            "classical_mean_dist": get_float(row, alias_map, "classical_mean_dist"),
            "planner_mean_dist": get_float(row, alias_map, "planner_mean_dist"),
            "paired_quantum_win_rate": get_float(row, alias_map, "paired_quantum_win_rate"),
            "_row_number": idx,
        }
        canonical["quantum_survival_pct"] = compute_survival_pct(
            canonical["shortest_path"], canonical["quantum_mean_dist"]
        )
        canonical["classical_survival_pct"] = compute_survival_pct(
            canonical["shortest_path"], canonical["classical_mean_dist"]
        )
        if (
            canonical["quantum_survival_pct"] is not None and
            canonical["classical_survival_pct"] is not None
        ):
            canonical["survival_lift_pct"] = (
                canonical["quantum_survival_pct"] - canonical["classical_survival_pct"]
            )
        else:
            canonical["survival_lift_pct"] = None
        canonical_rows.append(canonical)
    return canonical_rows


def determine_group_columns(rows: list[dict[str, object]], raw_group_by: str) -> list[str]:
    if raw_group_by != "auto":
        return [part.strip() for part in raw_group_by.split(",") if part.strip()]

    present = set()
    for row in rows:
        for key, value in row.items():
            if value not in (None, "") and not key.startswith("_"):
                present.add(key)

    group_cols: list[str] = []
    for column in ("run_id", "spec_mode", "bin_id", "bin_label"):
        if column in present:
            group_cols.append(column)
    if "spec_id" in present:
        group_cols.append("spec_id")
    else:
        for column in ("maze_dim", "latent_dim", "latent_gap", "side", "barriers", "gaps_per_barrier"):
            if column in present:
                group_cols.append(column)
    return group_cols or ["maze_dim", "latent_dim", "latent_gap"]


def group_key(row: dict[str, object], group_cols: list[str]) -> tuple[object, ...]:
    return tuple(row.get(column) for column in group_cols)


def validate_unique_mazes(rows: list[dict[str, object]], group_cols: list[str]) -> None:
    seen: set[tuple[object, ...]] = set()
    for row in rows:
        key = group_key(row, group_cols) + (row["maze_id"],)
        if key in seen:
            raise ValueError(
                "Found duplicate maze row within a confirmatory group: "
                f"group={key[:-1]!r}, maze_id={row['maze_id']!r}"
            )
        seen.add(key)


def mean_sem_ci(values: list[float], z_value: float) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    mean = float(np.mean(arr))
    if arr.size > 1:
        std = float(np.std(arr, ddof=1))
        sem = float(std / math.sqrt(arr.size))
    else:
        std = 0.0
        sem = 0.0
    return {
        "mean": mean,
        "std": std,
        "sem": sem,
        "ci_low": mean - z_value * sem,
        "ci_high": mean + z_value * sem,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def wilson_interval(successes: int, total: int, z_value: float) -> tuple[float, float]:
    if total == 0:
        return float("nan"), float("nan")
    phat = successes / total
    denom = 1.0 + (z_value ** 2) / total
    center = (phat + (z_value ** 2) / (2 * total)) / denom
    margin = (
        z_value
        * math.sqrt((phat * (1.0 - phat) / total) + (z_value ** 2) / (4 * total * total))
        / denom
    )
    return center - margin, center + margin


def summarize_group(rows: list[dict[str, object]], group_cols: list[str], z_value: float) -> dict[str, object]:
    first = rows[0]
    summary: dict[str, object] = {column: first.get(column) for column in group_cols}
    summary["n_rows"] = len(rows)
    summary["n_mazes"] = len({row["maze_id"] for row in rows})

    norm_stats = mean_sem_ci([float(row["paired_norm_adv_pct_mean"]) for row in rows], z_value)
    shortest_stats = mean_sem_ci([float(row["shortest_path"]) for row in rows], z_value)
    detour_stats = mean_sem_ci([float(row["detour_ratio"]) for row in rows], z_value)
    open_stats = mean_sem_ci([float(row["open_fraction"]) for row in rows], z_value)
    win_successes = sum(int(row["maze_quantum_win"]) for row in rows)
    win_low, win_high = wilson_interval(win_successes, len(rows), z_value)

    summary.update(
        {
            "normalized_adv_pct_mean": norm_stats["mean"],
            "normalized_adv_pct_sem": norm_stats["sem"],
            "normalized_adv_pct_ci_low": norm_stats["ci_low"],
            "normalized_adv_pct_ci_high": norm_stats["ci_high"],
            "normalized_adv_pct_min": norm_stats["min"],
            "normalized_adv_pct_max": norm_stats["max"],
            "maze_quantum_win_rate": win_successes / len(rows),
            "maze_quantum_win_ci_low": win_low,
            "maze_quantum_win_ci_high": win_high,
            "maze_quantum_wins": win_successes,
            "shortest_path_mean": shortest_stats["mean"],
            "shortest_path_ci_low": shortest_stats["ci_low"],
            "shortest_path_ci_high": shortest_stats["ci_high"],
            "shortest_path_min": shortest_stats["min"],
            "shortest_path_max": shortest_stats["max"],
            "detour_ratio_mean": detour_stats["mean"],
            "detour_ratio_ci_low": detour_stats["ci_low"],
            "detour_ratio_ci_high": detour_stats["ci_high"],
            "detour_ratio_min": detour_stats["min"],
            "detour_ratio_max": detour_stats["max"],
            "open_fraction_mean": open_stats["mean"],
            "open_fraction_ci_low": open_stats["ci_low"],
            "open_fraction_ci_high": open_stats["ci_high"],
            "open_fraction_min": open_stats["min"],
            "open_fraction_max": open_stats["max"],
        }
    )

    if all(row["paired_raw_adv_mean"] is not None for row in rows):
        raw_stats = mean_sem_ci([float(row["paired_raw_adv_mean"]) for row in rows], z_value)
        summary.update(
            {
                "raw_adv_mean": raw_stats["mean"],
                "raw_adv_sem": raw_stats["sem"],
                "raw_adv_ci_low": raw_stats["ci_low"],
                "raw_adv_ci_high": raw_stats["ci_high"],
                "raw_adv_min": raw_stats["min"],
                "raw_adv_max": raw_stats["max"],
            }
        )

    if all(row.get("quantum_survival_pct") is not None for row in rows):
        q_survival = mean_sem_ci([float(row["quantum_survival_pct"]) for row in rows], z_value)
        summary.update(
            {
                "quantum_survival_pct_mean": q_survival["mean"],
                "quantum_survival_pct_sem": q_survival["sem"],
                "quantum_survival_pct_ci_low": q_survival["ci_low"],
                "quantum_survival_pct_ci_high": q_survival["ci_high"],
            }
        )

    if all(row.get("classical_survival_pct") is not None for row in rows):
        c_survival = mean_sem_ci([float(row["classical_survival_pct"]) for row in rows], z_value)
        summary.update(
            {
                "classical_survival_pct_mean": c_survival["mean"],
                "classical_survival_pct_sem": c_survival["sem"],
                "classical_survival_pct_ci_low": c_survival["ci_low"],
                "classical_survival_pct_ci_high": c_survival["ci_high"],
            }
        )

    if all(row.get("survival_lift_pct") is not None for row in rows):
        lift_stats = mean_sem_ci([float(row["survival_lift_pct"]) for row in rows], z_value)
        summary.update(
            {
                "survival_lift_pct_mean": lift_stats["mean"],
                "survival_lift_pct_sem": lift_stats["sem"],
                "survival_lift_pct_ci_low": lift_stats["ci_low"],
                "survival_lift_pct_ci_high": lift_stats["ci_high"],
            }
        )

    for metric in OPTIONAL_NUMERIC:
        if metric in ("paired_raw_adv_mean",):
            continue
        if all(row.get(metric) is not None for row in rows):
            stats = mean_sem_ci([float(row[metric]) for row in rows], z_value)
            stem = metric
            summary[f"{stem}_mean"] = stats["mean"]
            summary[f"{stem}_sem"] = stats["sem"]
            summary[f"{stem}_ci_low"] = stats["ci_low"]
            summary[f"{stem}_ci_high"] = stats["ci_high"]

    return summary


def summarize_rows(rows: list[dict[str, object]], group_cols: list[str], z_value: float) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row, group_cols)].append(row)

    summaries = [
        summarize_group(group_rows, group_cols, z_value)
        for _, group_rows in sorted(grouped.items(), key=lambda item: item[0])
    ]
    return summaries


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.4f}"
    return str(value)


def write_csv_summary(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty summary")
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(value) for key, value in row.items()})


def markdown_table(rows: list[dict[str, object]], group_cols: list[str]) -> str:
    headers = group_cols + [
        "n_mazes",
        "normalized_adv_pct_mean",
        "normalized_adv_pct_ci_low",
        "normalized_adv_pct_ci_high",
        "survival_lift_pct_mean",
        "survival_lift_pct_ci_low",
        "survival_lift_pct_ci_high",
        "maze_quantum_win_rate",
        "maze_quantum_win_ci_low",
        "maze_quantum_win_ci_high",
        "detour_ratio_mean",
        "open_fraction_mean",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_value(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def write_markdown_report(
    path: Path,
    input_path: Path,
    rows: list[dict[str, object]],
    summaries: list[dict[str, object]],
    group_cols: list[str],
) -> None:
    total_groups = len(summaries)
    total_mazes = len(rows)
    report = [
        "# Maze Scaling Confirmatory Summary",
        "",
        f"- Source CSV: `{input_path}`",
        f"- Per-maze rows loaded: `{total_mazes}`",
        f"- Confirmatory groups: `{total_groups}`",
        f"- Group columns: `{', '.join(group_cols)}`",
        "",
        "## Confirmatory Table",
        "",
        markdown_table(summaries, group_cols),
        "",
        "## Notes",
        "",
        "- Unit of inference: maze.",
        "- Headline effect: per-maze normalized advantage, then grouped across mazes.",
        "- Maze win rate uses a Wilson interval.",
        "- Mean intervals use normal-approximation SEM intervals with the chosen z value.",
        "- Trial-level outcomes are intentionally not treated as independent confirmatory samples.",
    ]
    path.write_text("\n".join(report) + "\n")


def print_console_summary(summaries: list[dict[str, object]], group_cols: list[str]) -> None:
    print("=" * 100)
    print("  MAZE SCALING CONFIRMATORY SUMMARY")
    print("=" * 100)
    headers = group_cols + ["n_mazes", "norm_adv", "survival", "win_rate", "detour", "open"]
    print("  " + " | ".join(f"{header:>12}" for header in headers))
    print("  " + "-" * 96)
    for row in summaries:
        values = [format_value(row.get(column, "")) for column in group_cols]
        survival_value = "n/a"
        if "survival_lift_pct_mean" in row:
            survival_value = (
                f"{row['survival_lift_pct_mean']:+.2f}% "
                f"[{row['survival_lift_pct_ci_low']:+.2f}, {row['survival_lift_pct_ci_high']:+.2f}]"
            )
        values.extend(
            [
                format_value(row["n_mazes"]),
                f"{row['normalized_adv_pct_mean']:+.2f}%",
                survival_value,
                f"{row['maze_quantum_win_rate']:.1%}",
                f"{row['detour_ratio_mean']:.2f}x",
                f"{row['open_fraction_mean']:.2f}",
            ]
        )
        print("  " + " | ".join(f"{value:>12}" for value in values))


def main() -> None:
    args = parse_args()
    raw_rows = parse_csv(args.csv_path)
    alias_map = resolve_aliases(raw_rows[0].keys())
    require_schema(alias_map)
    rows = canonicalize_rows(raw_rows, alias_map)
    group_cols = determine_group_columns(rows, args.group_by)
    validate_unique_mazes(rows, group_cols)
    summaries = summarize_rows(rows, group_cols, args.ci_z)

    print_console_summary(summaries, group_cols)

    if args.summary_csv_out is not None:
        write_csv_summary(args.summary_csv_out, summaries)
        print(f"\nwrote_summary_csv        : {args.summary_csv_out}")

    if args.summary_md_out is not None:
        write_markdown_report(args.summary_md_out, args.csv_path, rows, summaries, group_cols)
        print(f"wrote_summary_markdown   : {args.summary_md_out}")


if __name__ == "__main__":
    main()
