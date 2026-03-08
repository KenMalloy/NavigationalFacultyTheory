#!/usr/bin/env python3
"""Split book_v2.md into individual chapter files in book_v2/chapters/.

Delimiter-based: splits on heading patterns, not hardcoded line numbers.
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(REPO_ROOT, "book_v2.md")
OUTDIR = os.path.join(REPO_ROOT, "book_v2", "chapters")

# Each entry: (filename, delimiter_pattern)
# The delimiter is the FIRST line that belongs to this chapter.
# Everything from this delimiter up to (but not including) the next delimiter
# belongs to this chapter.
CHAPTERS = [
    ("00_preface.md",           r"^# The Navigational Faculty"),
    ("01_hard_problem.md",      r"^# PART ONE:"),
    ("02_structurally_hard.md", r"^## Chapter 2:"),
    ("03_testability.md",       r"^## Chapter 3:"),
    ("04_navigation.md",        r"^# PART TWO:"),
    ("05_entropic_current.md",  r"^## Chapter 5:"),
    ("06_evolutionary_case.md", r"^## Chapter 6:"),
    ("07_categorical_difference.md", r"^# PART THREE:"),
    ("08_honest_path.md",       r"^## Chapter 8:"),
    ("09_how_sculpting_works.md", r"^## Chapter 9:"),
    ("10_navigation_proof.md",  r"^## Chapter 10:"),
    ("11_zeno.md",              r"^# PART FOUR:"),
    ("12_qualia.md",            r"^## Chapter 12:"),
    ("13_binding_topology.md",  r"^## Chapter 13:"),
    ("14_possibility_space.md", r"^# PART FIVE:"),
    ("15_experimental_program.md", r"^# PART SIX:"),
    ("16_implications.md",      r"^## Chapter 16:"),
    ("17_formalization.md",     r"^## Chapter 17:"),
    ("18_epilogue.md",          r"^# Epilogue:"),
    ("19_appendices.md",        r"^# Appendices"),
]


def find_line(lines, pattern, after=0):
    """Find the first line matching pattern at or after the given index."""
    regex = re.compile(pattern)
    for i in range(after, len(lines)):
        if regex.match(lines[i]):
            return i
    return None


def split():
    with open(MASTER, "r") as f:
        lines = f.read().split("\n")

    os.makedirs(OUTDIR, exist_ok=True)

    # Find the start line for each chapter
    starts = []
    search_from = 0
    for fname, pattern in CHAPTERS:
        idx = find_line(lines, pattern, after=search_from)
        if idx is None:
            print(f"ERROR: pattern {pattern!r} not found for {fname}")
            return 1
        starts.append((fname, idx))
        search_from = idx + 1

    # Each chapter includes a leading --- separator if one exists
    # on the line(s) immediately before its delimiter
    for i, (fname, start) in enumerate(starts):
        # Walk backwards to include preceding --- and blank lines
        while start > 0 and lines[start - 1].strip() in ("---", ""):
            # But don't eat into the previous chapter's content
            if i > 0 and start - 1 <= starts[i - 1][1]:
                break
            start -= 1
        starts[i] = (fname, start)

    # Write each chapter
    for i, (fname, start) in enumerate(starts):
        if i + 1 < len(starts):
            end = starts[i + 1][1]
        else:
            end = len(lines)

        chunk = "\n".join(lines[start:end]).strip() + "\n"
        path = os.path.join(OUTDIR, fname)
        with open(path, "w") as out:
            out.write(chunk)

    print(f"split_chapters: {len(starts)} files written to {OUTDIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(split())
