#!/usr/bin/env python3
"""Render the book manuscript to a styled PDF via HTML and Chrome."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ORDERED_LIST_RE = re.compile(r"^(\d+)\.\s+(.*)$")
UNORDERED_LIST_RE = re.compile(r"^[-*]\s+(.*)$")
TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$")
TABLE_ALIGN_RE = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
THEMATIC_BREAK_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
STRONG_EM_RE = re.compile(r"\*\*\*([^*]+)\*\*\*")
STRONG_RE = re.compile(r"\*\*([^*]+)\*\*")
EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
URL_RE = re.compile(r"https?://[^\s<]+")


CSS = """
@page {
  size: Letter;
  margin: 0.72in 0.8in;
}

:root {
  --paper: #fffdf8;
  --ink: #1f1c18;
  --muted: #6d665d;
  --rule: #d6d0c7;
  --table-fill: #f6f1e8;
  --link: #1b4f8a;
}

html {
  background: var(--paper);
}

body {
  margin: 0;
  color: var(--ink);
  background: var(--paper);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}

.book {
  max-width: 7.1in;
  margin: 0 auto;
}

h1, h2, h3, h4, h5, h6 {
  color: #16120f;
  font-family: "Baskerville", "Times New Roman", serif;
  font-weight: 700;
  line-height: 1.12;
  margin: 1.8rem 0 0.75rem;
  break-after: avoid-page;
}

h1 {
  font-size: 28pt;
  break-before: page;
}

h2 {
  font-size: 20pt;
}

h3 {
  font-size: 15pt;
  margin-top: 1.4rem;
}

h4, h5, h6 {
  font-size: 12.5pt;
}

.book > h1:first-of-type {
  break-before: auto;
  margin-top: 1.8rem;
  text-align: center;
}

.book > h1:first-of-type + h2,
.book > h1:first-of-type + h2 + h3 {
  text-align: center;
  color: var(--muted);
  font-weight: 500;
}

.book > h1:first-of-type + h2 {
  margin-top: 0.9rem;
}

.book > h1:first-of-type + h2 + h3 {
  margin-top: 0.3rem;
}

h1.part-title,
h2.chapter-title {
  break-before: page;
}

p,
li {
  font-size: 11.5pt;
  line-height: 1.62;
  margin: 0.72rem 0;
  orphans: 3;
  widows: 3;
}

ul,
ol {
  margin: 0.85rem 0 0.85rem 1.35rem;
  padding: 0;
}

li + li {
  margin-top: 0.18rem;
}

hr {
  border: 0;
  border-top: 1px solid var(--rule);
  margin: 1.8rem 0;
}

strong {
  font-weight: 700;
}

em {
  font-style: italic;
}

code {
  font-family: "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 0.9em;
  background: #f1ede6;
  border-radius: 3px;
  padding: 0.08em 0.28em;
}

a {
  color: var(--link);
  text-decoration: none;
  word-break: break-word;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0 1.4rem;
  font-size: 10.5pt;
  break-inside: avoid-page;
}

thead {
  break-inside: avoid-page;
}

th,
td {
  border: 1px solid var(--rule);
  padding: 0.42rem 0.55rem;
  text-align: left;
  vertical-align: top;
}

thead th {
  background: var(--table-fill);
  font-weight: 700;
}

blockquote {
  margin: 1rem 0 1rem 1.1rem;
  padding-left: 0.9rem;
  border-left: 3px solid var(--rule);
  color: #4f4b45;
}
""".strip()


def inline_html(text: str) -> str:
    code_segments: list[str] = []

    def replace_code(match: re.Match[str]) -> str:
        code_segments.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        return f"@@CODE{len(code_segments) - 1}@@"

    def restore_code(rendered: str) -> str:
        for index, segment in enumerate(code_segments):
            rendered = rendered.replace(f"@@CODE{index}@@", segment)
        return rendered

    def replace_url(match: re.Match[str]) -> str:
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,;:!?":
            trailing = url[-1] + trailing
            url = url[:-1]
        return f'<a href="{url}">{url}</a>{trailing}'

    rendered = INLINE_CODE_RE.sub(replace_code, text)
    rendered = html.escape(rendered, quote=False)
    rendered = STRONG_EM_RE.sub(r"<strong><em>\1</em></strong>", rendered)
    rendered = STRONG_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = EM_RE.sub(r"<em>\1</em>", rendered)
    rendered = URL_RE.sub(replace_url, rendered)
    return restore_code(rendered)


def paragraph_html(lines: list[str]) -> str:
    collapsed = " ".join(line.strip() for line in lines)
    return f"<p>{inline_html(collapsed)}</p>"


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def table_alignments(line: str) -> list[str]:
    alignments = []
    for cell in split_table_row(line):
        stripped = cell.strip()
        if stripped.startswith(":") and stripped.endswith(":"):
            alignments.append("center")
        elif stripped.endswith(":"):
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments


def heading_class(level: int, text: str) -> str:
    plain = text.strip()
    if level == 1 and plain.startswith("PART "):
        return "part-title"
    if level == 2 and plain.startswith("Chapter "):
        return "chapter-title"
    return ""


def render_markdown(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    blocks: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if THEMATIC_BREAK_RE.match(stripped):
            blocks.append("<hr>")
            i += 1
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            content = inline_html(heading_match.group(2).strip())
            klass = heading_class(level, heading_match.group(2))
            class_attr = f' class="{klass}"' if klass else ""
            blocks.append(f"<h{level}{class_attr}>{content}</h{level}>")
            i += 1
            continue

        if TABLE_ROW_RE.match(line) and i + 1 < len(lines) and TABLE_ALIGN_RE.match(lines[i + 1]):
            headers = split_table_row(line)
            alignments = table_alignments(lines[i + 1])
            i += 2
            body_rows: list[list[str]] = []
            while i < len(lines) and TABLE_ROW_RE.match(lines[i].strip()):
                body_rows.append(split_table_row(lines[i]))
                i += 1

            table_parts = ["<table>", "<thead><tr>"]
            for idx, header in enumerate(headers):
                align = alignments[idx] if idx < len(alignments) else "left"
                table_parts.append(
                    f'<th style="text-align: {align};">{inline_html(header)}</th>'
                )
            table_parts.append("</tr></thead>")

            if body_rows:
                table_parts.append("<tbody>")
                for row in body_rows:
                    table_parts.append("<tr>")
                    for idx, cell in enumerate(row):
                        align = alignments[idx] if idx < len(alignments) else "left"
                        table_parts.append(
                            f'<td style="text-align: {align};">{inline_html(cell)}</td>'
                        )
                    table_parts.append("</tr>")
                table_parts.append("</tbody>")

            table_parts.append("</table>")
            blocks.append("".join(table_parts))
            continue

        unordered_match = UNORDERED_LIST_RE.match(line)
        if unordered_match:
            items = []
            while i < len(lines):
                match = UNORDERED_LIST_RE.match(lines[i])
                if not match:
                    break
                items.append(f"<li>{inline_html(match.group(1).strip())}</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue

        ordered_match = ORDERED_LIST_RE.match(line)
        if ordered_match:
            items = []
            while i < len(lines):
                match = ORDERED_LIST_RE.match(lines[i])
                if not match:
                    break
                items.append(f"<li>{inline_html(match.group(2).strip())}</li>")
                i += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue

        if line.lstrip().startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].lstrip().startswith("> "):
                quote_lines.append(lines[i].lstrip()[2:])
                i += 1
            blocks.append(f"<blockquote>{paragraph_html(quote_lines)}</blockquote>")
            continue

        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            next_stripped = next_line.strip()
            if not next_stripped:
                break
            if (
                THEMATIC_BREAK_RE.match(next_stripped)
                or HEADING_RE.match(next_line)
                or (
                    TABLE_ROW_RE.match(next_line)
                    and i + 1 < len(lines)
                    and TABLE_ALIGN_RE.match(lines[i + 1])
                )
                or UNORDERED_LIST_RE.match(next_line)
                or ORDERED_LIST_RE.match(next_line)
                or next_line.lstrip().startswith("> ")
            ):
                break
            paragraph_lines.append(next_line)
            i += 1

        blocks.append(paragraph_html(paragraph_lines))

    return "\n".join(blocks)


def wrap_html(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
{CSS}
  </style>
</head>
<body>
  <main class="book">
{body_html}
  </main>
</body>
</html>
"""


def chrome_binary() -> Path:
    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Google Chrome or Chromium is required to print the PDF")


def print_pdf(html_path: Path, pdf_path: Path, paper_format: str) -> None:
    del paper_format  # CSS @page controls the final paper size.

    browser = chrome_binary()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.unlink(missing_ok=True)

    user_data_dir = Path(tempfile.mkdtemp(prefix="book-pdf-chrome-"))
    command = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--disable-crash-reporter",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--user-data-dir={user_data_dir}",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]

    try:
        process = subprocess.Popen(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 45
        last_size = -1
        stable_for = 0.0

        while time.monotonic() < deadline:
            status = process.poll()
            if pdf_path.is_file():
                current_size = pdf_path.stat().st_size
                if current_size > 0 and current_size == last_size:
                    stable_for += 0.5
                else:
                    stable_for = 0.0
                    last_size = current_size

                if current_size > 0 and stable_for >= 2.0:
                    if status is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    break

            if status is not None:
                break

            time.sleep(0.5)

        if process.poll() is None:
            if pdf_path.is_file() and pdf_path.stat().st_size > 0:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            else:
                process.kill()
                process.wait(timeout=5)
                raise RuntimeError("chrome timed out before producing a PDF")

        stdout, stderr = process.communicate()
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)

    if process.returncode not in (0, -15):
        stderr = stderr.strip() or stdout.strip()
        raise RuntimeError(f"chrome headless print failed: {stderr}")

    if not pdf_path.is_file():
        raise RuntimeError("chrome completed without producing the PDF file")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default="book_v2.md",
        help="Markdown source file to render",
    )
    parser.add_argument(
        "--output",
        default="book.pdf",
        help="Path for the generated PDF",
    )
    parser.add_argument(
        "--html-output",
        help="Optional path to keep the intermediate HTML",
    )
    parser.add_argument(
        "--paper-format",
        default="Letter",
        choices=["Letter", "Legal", "Tabloid", "Ledger", "A0", "A1", "A2", "A3", "A4", "A5", "A6"],
        help="Paper format passed to Playwright",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    markdown_text = input_path.read_text(encoding="utf-8")
    body_html = render_markdown(markdown_text)
    document_html = wrap_html(input_path.stem, body_html)

    html_output = Path(args.html_output).resolve() if args.html_output else None

    if html_output:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(document_html, encoding="utf-8")
        html_path = html_output
        cleanup_html = False
    else:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            delete=False,
            encoding="utf-8",
        ) as handle:
            handle.write(document_html)
            html_path = Path(handle.name)
        cleanup_html = True

    try:
        print_pdf(html_path, output_path, args.paper_format)
    finally:
        if cleanup_html:
            html_path.unlink(missing_ok=True)

    print(f"Rendered {input_path.name} -> {output_path}")
    if html_output:
        print(f"Intermediate HTML: {html_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
