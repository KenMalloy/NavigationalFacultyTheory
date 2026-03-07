#!/usr/bin/env python3
"""Split book_draft_v2.md into individual chapter files in book_v2/chapters/."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(REPO_ROOT, "book_draft_v2.md")
OUTDIR = os.path.join(REPO_ROOT, "book_v2", "chapters")

CHAPTERS = [
    ("00_preface.md", 1, 98),
    ("01_hard_problem.md", 99, 150),
    ("02_structurally_hard.md", 151, 174),
    ("03_testability.md", 175, 226),
    ("04_navigation.md", 227, 284),
    ("05_entropic_current.md", 285, 328),
    ("06_evolutionary_case.md", 329, 374),
    ("07_categorical_difference.md", 375, 412),
    ("08_honest_path.md", 413, 482),
    ("09_how_sculpting_works.md", 483, 581),
    ("10_navigation_proof.md", 582, 673),
    ("11_zeno.md", 674, 713),
    ("12_qualia.md", 714, 783),
    ("13_binding_topology.md", 784, 829),
    ("14_possibility_space.md", 830, 878),
    ("15_experimental_program.md", 879, 948),
    ("16_implications.md", 949, 1047),
    ("17_formalization.md", 1048, 1091),
    ("18_epilogue.md", 1092, 1117),
    ("19_appendices.md", 1118, None),  # None = end of file
]


def split():
    with open(MASTER, "r") as f:
        lines = f.read().split("\n")

    os.makedirs(OUTDIR, exist_ok=True)

    for fname, start, end in CHAPTERS:
        if end is None:
            end = len(lines)
        chunk = "\n".join(lines[start - 1 : end]).strip() + "\n"
        path = os.path.join(OUTDIR, fname)
        with open(path, "w") as out:
            out.write(chunk)

    print(f"split_chapters: {len(CHAPTERS)} files written to {OUTDIR}")


if __name__ == "__main__":
    split()
