#!/usr/bin/env python3
"""Build audiobook-ready transcript artifacts inside the audiobook folder."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SOURCE = REPO_ROOT / "book_v2.md"
DEFAULT_BUILD_DIR = SCRIPT_DIR / "build"
DEFAULT_OVERRIDES = SCRIPT_DIR / "lexicon_overrides.json"
DEFAULT_FRONT_MATTER = SCRIPT_DIR / "front_matter.json"
DEFAULT_TTS_INSTRUCTIONS = (
    "Narrate as a calm, deliberate nonfiction audiobook. The tone is warm and "
    "intellectually confident — a knowledgeable author speaking directly to a "
    "curious reader. Allow conviction and warmth to rise in philosophical and "
    "personal passages without becoming dramatic. Slow slightly and articulate "
    "clearly for sentences dense with technical terms. For quoted passages, adopt "
    "a subtly more formal register. When a sentence begins with 'Term note:', "
    "read it as a brief, matter-of-fact aside before returning to the normal "
    "voice. When a long, dense sentence is followed by a short sentence that "
    "lands a point, give the short sentence a clear natural pause before and "
    "after it. Add a natural pause before and after chapter and part headings."
)

START_HEADING = "# Preface: How to Read This Book"
END_HEADING = "# Appendices"

TAG_REPLACEMENTS = {
    "[A]": "Level A",
    "[B]": "Level B",
    "[C]": "Level C",
}

# Curated phrases that earn a dramatic pause (\n\n) before them.
# Matched against normalized speech_text (markdown stripped, em-dashes → commas).
DRAMATIC_PAUSE_PHRASES: list[str] = [
    # The lights motif (bookends)
    "The lights come on.",
    "The lights go out, the machine keeps running.",
    "Tomorrow morning you will wake up and the lights will come on.",
    # Landing sentences after buildup
    "There is something it is like to hear a door slam.",
    "Three decades later, the gap has not narrowed, though it has become better documented.",
    "They were never in separate rooms.",
    "Heat is not the purpose of friction; it is the physics.",
    "It was five thousand times longer.",
    "It was kind of a big deal.",
    "The information isn't in the cufflink.",
    "The agency is in what gets asked.",
    "Rhodopsin shows you the world. The loop puts you in it.",
    "A framework that has never been wrong has never been tested.",
    "This book is an invitation to do them.",
    "You are navigating, you always have been, and the world is different for your having walked it.",
    # Philosophical gut-punches
    "Why it feels like something rather than nothing.",
    "A wake is not a ship.",
    "The machine has no yesterday.",
    # Floor-drop moments
    "We tested it. The results were unambiguous.",
    "The original headline collapsed.",
    "The prediction was not supported.",
    # Register shift
    "Your name is the first thing to go.",
    # Dial-turners
    "Consciousness is a dial, and the loop is what the dial turns.",
    "The terrain and the navigator co-emerge.",
    "Freedom pays.",
]


@dataclass
class Block:
    kind: str
    text: str
    source_start_line: int
    source_end_line: int
    heading_level: int | None = None
    heading_text: str | None = None
    section_path: list[str] = field(default_factory=list)
    first_use_notes: list[str] = field(default_factory=list)
    speech_text: str = ""
    tts_text: str = ""


@dataclass
class GlossaryEntry:
    term: str
    description: str
    spoken: str | None = None
    pronunciation_note: str | None = None
    expansion: str | None = None
    first_use_note: str | None = None


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def extract_scope(lines: list[str]) -> tuple[list[tuple[int, str]], int, int]:
    start_index = next(
        (index for index, line in enumerate(lines) if line.strip() == START_HEADING),
        None,
    )
    if start_index is None:
        raise ValueError(f"Could not find start heading: {START_HEADING}")

    end_index = next(
        (
            index
            for index in range(start_index + 1, len(lines))
            if lines[index].strip() == END_HEADING
        ),
        None,
    )
    if end_index is None:
        raise ValueError(f"Could not find end heading: {END_HEADING}")

    scoped = [(index + 1, lines[index]) for index in range(start_index, end_index)]
    return scoped, start_index + 1, end_index + 1


def parse_blocks(scoped_lines: list[tuple[int, str]]) -> list[Block]:
    blocks: list[Block] = []
    index = 0

    while index < len(scoped_lines):
        line_number, line = scoped_lines[index]
        stripped = line.strip()

        if not stripped or is_horizontal_rule(stripped):
            index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            blocks.append(
                Block(
                    kind="heading",
                    text=heading_match.group(2).strip(),
                    heading_level=len(heading_match.group(1)),
                    heading_text=heading_match.group(2).strip(),
                    source_start_line=line_number,
                    source_end_line=line_number,
                )
            )
            index += 1
            continue

        if stripped.startswith("```"):
            start_line = line_number
            chunk = [line]
            index += 1
            while index < len(scoped_lines):
                current_line_number, current_line = scoped_lines[index]
                chunk.append(current_line)
                index += 1
                if current_line.strip().startswith("```"):
                    blocks.append(
                        Block(
                            kind="code",
                            text="\n".join(chunk),
                            source_start_line=start_line,
                            source_end_line=current_line_number,
                        )
                    )
                    break
            else:
                blocks.append(
                    Block(
                        kind="code",
                        text="\n".join(chunk),
                        source_start_line=start_line,
                        source_end_line=scoped_lines[-1][0],
                    )
                )
            continue

        if is_table_row(stripped):
            start_line = line_number
            table_lines = [line]
            index += 1
            while index < len(scoped_lines):
                _, current_line = scoped_lines[index]
                current_stripped = current_line.strip()
                if not current_stripped or not is_table_row(current_stripped):
                    break
                table_lines.append(current_line)
                index += 1
            blocks.append(
                Block(
                    kind="table",
                    text="\n".join(table_lines),
                    source_start_line=start_line,
                    source_end_line=scoped_lines[index - 1][0],
                )
            )
            continue

        if is_list_item(stripped):
            start_line = line_number
            list_lines = [line]
            index += 1
            while index < len(scoped_lines):
                _, current_line = scoped_lines[index]
                current_stripped = current_line.strip()
                if not current_stripped:
                    break
                if is_list_item(current_stripped) or current_line.startswith("  "):
                    list_lines.append(current_line)
                    index += 1
                    continue
                break
            blocks.append(
                Block(
                    kind="list",
                    text="\n".join(list_lines),
                    source_start_line=start_line,
                    source_end_line=scoped_lines[index - 1][0],
                )
            )
            continue

        if stripped.startswith(">"):
            start_line = line_number
            quote_lines = [line]
            index += 1
            while index < len(scoped_lines):
                _, current_line = scoped_lines[index]
                if not current_line.strip().startswith(">"):
                    break
                quote_lines.append(current_line)
                index += 1
            blocks.append(
                Block(
                    kind="quote",
                    text="\n".join(quote_lines),
                    source_start_line=start_line,
                    source_end_line=scoped_lines[index - 1][0],
                )
            )
            continue

        start_line = line_number
        paragraph_lines = [line]
        index += 1
        while index < len(scoped_lines):
            next_line_number, next_line = scoped_lines[index]
            next_stripped = next_line.strip()
            if not next_stripped:
                break
            if is_horizontal_rule(next_stripped):
                break
            if re.match(r"^(#{1,6})\s+", next_stripped):
                break
            if next_stripped.startswith("```"):
                break
            if is_table_row(next_stripped):
                break
            if is_list_item(next_stripped):
                break
            paragraph_lines.append(next_line)
            index += 1
        blocks.append(
            Block(
                kind="paragraph",
                text="\n".join(paragraph_lines),
                source_start_line=start_line,
                source_end_line=scoped_lines[index - 1][0],
            )
        )

    return blocks


def is_horizontal_rule(text: str) -> bool:
    return text in {"---", "***", "___"}


def is_table_row(text: str) -> bool:
    cells = [cell.strip() for cell in text.strip("|").split("|")]
    return "|" in text and len(cells) >= 2


def is_list_item(text: str) -> bool:
    return bool(re.match(r"^([-*+]|\d+\.)\s+", text))


def extract_glossary(blocks: list[Block]) -> tuple[list[Block], dict[str, GlossaryEntry]]:
    cleaned_blocks: list[Block] = []
    entries: dict[str, GlossaryEntry] = {}
    in_glossary = False

    for block in blocks:
        if block.kind == "heading" and block.heading_text == "Glossary of Key Terms":
            in_glossary = True
            continue

        if in_glossary and block.kind == "heading" and block.heading_level == 1:
            in_glossary = False

        if in_glossary:
            if block.kind == "paragraph":
                entry = parse_glossary_entry(block.text)
                if entry:
                    entries[entry.term] = entry
            continue

        cleaned_blocks.append(block)

    return cleaned_blocks, entries


def parse_glossary_entry(text: str) -> GlossaryEntry | None:
    compact = " ".join(text.split())

    note_match = re.match(r"^\*\*(.+?)\*\*\s*\((.+?)\)\.\s*(.+)$", compact)
    if note_match:
        term = note_match.group(1).strip()
        note = note_match.group(2).strip()
        description = note_match.group(3).strip()
        return GlossaryEntry(
            term=term,
            description=description,
            spoken=spoken_from_pronunciation(note),
            pronunciation_note=note,
        )

    standard_match = re.match(r"^\*\*(.+?)\.\*\*\s*(.+)$", compact)
    if standard_match:
        term = standard_match.group(1).strip()
        description = standard_match.group(2).strip()
        return GlossaryEntry(
            term=term,
            description=description,
            spoken=spoken_for_term(term),
            expansion=expansion_from_description(description, term),
        )

    return None


def spoken_from_pronunciation(note: str) -> str:
    return note.split(",", 1)[0].strip()


def spoken_for_term(term: str) -> str | None:
    if re.fullmatch(r"[A-Z]{2,}", term):
        return " ".join(term)
    return None


def expansion_from_description(description: str, term: str) -> str | None:
    if not re.fullmatch(r"[A-Z]{2,}", term):
        return None
    match = re.match(r"^([A-Z][A-Za-z' -]+?)(?:\s*\(|\.)", description)
    if not match:
        return None
    expansion = match.group(1).strip()
    return expansion if expansion and expansion != term else None


def apply_overrides(
    entries: dict[str, GlossaryEntry],
    overrides_path: Path,
) -> dict[str, GlossaryEntry]:
    if not overrides_path.exists():
        return entries

    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    merged = dict(entries)

    for term, override in overrides.items():
        current = merged.get(term, GlossaryEntry(term=term, description=""))
        merged[term] = GlossaryEntry(
            term=term,
            description=current.description,
            spoken=override.get("spoken", current.spoken),
            pronunciation_note=override.get(
                "pronunciation_note", current.pronunciation_note
            ),
            expansion=override.get("expansion", current.expansion),
            first_use_note=override.get("first_use_note", current.first_use_note),
        )

    return merged


def load_front_matter(path: Path) -> list[Block]:
    if not path.exists():
        return []

    payload = json.loads(path.read_text(encoding="utf-8"))
    blocks: list[Block] = []
    synthetic_line = 0

    for item in payload:
        kind = item["kind"]
        text = item["text"].strip()
        blocks.append(
            Block(
                kind=kind,
                text=text,
                heading_level=1 if kind == "heading" else None,
                heading_text=text if kind == "heading" else None,
                source_start_line=synthetic_line,
                source_end_line=synthetic_line,
            )
        )
        synthetic_line -= 1

    return blocks


def assign_sections(blocks: list[Block]) -> None:
    section_stack: list[tuple[int, str]] = []
    for block in blocks:
        if block.kind == "heading" and block.heading_level is not None:
            while section_stack and section_stack[-1][0] >= block.heading_level:
                section_stack.pop()
            section_stack.append((block.heading_level, block.heading_text or ""))
        block.section_path = [title for _, title in section_stack]


def normalize_blocks(blocks: list[Block]) -> None:
    for block in blocks:
        if block.kind == "heading":
            block.speech_text = normalize_heading(block.heading_text or "")
        elif block.kind == "paragraph":
            block.speech_text = apply_dramatic_pauses(apply_pacing_breaks(normalize_inline_markdown(block.text)))
        elif block.kind == "list":
            block.speech_text = normalize_list(block.text)
        elif block.kind == "table":
            block.speech_text = normalize_table(block.text)
        elif block.kind == "code":
            block.speech_text = (
                "A code example appears here. In the audiobook edition, the code "
                "itself is not read line by line."
            )
        elif block.kind == "quote":
            quote_text = apply_dramatic_pauses(apply_pacing_breaks(
                normalize_inline_markdown(
                "\n".join(line.lstrip("> ").rstrip() for line in block.text.splitlines())
                )
            ))
            block.speech_text = f"Quoted passage. {quote_text}"
        else:
            block.speech_text = normalize_inline_markdown(block.text)


def normalize_heading(text: str) -> str:
    if ":" in text:
        left, right = text.split(":", 1)
        return f"{left.strip()}. {right.strip()}."
    return f"{text.strip()}."


def normalize_list(text: str) -> str:
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^([-*+]|\d+\.)\s+(.*)$", stripped)
        if match:
            items.append(normalize_inline_markdown(match.group(2)))
        elif items:
            items[-1] = f"{items[-1]} {normalize_inline_markdown(stripped)}"
    rendered = [f"Item {index}: {item}" for index, item in enumerate(items, start=1)]
    return " ".join(rendered)


def normalize_table(text: str) -> str:
    parsed = parse_markdown_table(text)
    headers = parsed["headers"]
    rows = parsed["rows"]

    if not headers and not rows:
        return "A table appears here."

    if headers and rows and len(headers) <= 4 and len(rows) <= 4:
        return narrate_small_table(headers, rows)

    if headers and rows:
        preview = " ".join(
            narrate_table_row(headers, row, index + 1)
            for index, row in enumerate(rows[:3])
        )
        summary = (
            f"The following table compares {', '.join(headers)}. "
            f"It contains {len(rows)} rows, so this audiobook summarizes the "
            "main pattern instead of reading every cell. "
        )
        if len(rows) > 3:
            summary += "Here are the first few rows. "
        return summary + preview

    if headers:
        return f"A table appears here. The column headings are: {', '.join(headers)}."

    return "A table appears here."


def parse_markdown_table(text: str) -> dict[str, list[list[str]] | list[str]]:
    raw_rows = [line.strip() for line in text.splitlines() if line.strip()]
    parsed_rows = [split_markdown_row(row) for row in raw_rows]
    parsed_rows = [row for row in parsed_rows if row]
    if not parsed_rows:
        return {"headers": [], "rows": []}

    headers = parsed_rows[0]
    body_rows = [
        row for row in parsed_rows[1:] if not is_markdown_separator_row(row)
    ]
    return {"headers": headers, "rows": body_rows}


def split_markdown_row(row: str) -> list[str]:
    return [normalize_inline_markdown(cell) for cell in row.strip("|").split("|")]


def is_markdown_separator_row(row: list[str]) -> bool:
    return bool(row) and all(re.fullmatch(r"[:\- ]+", cell) for cell in row)


def narrate_small_table(headers: list[str], rows: list[list[str]]) -> str:
    intro = f"The following table reports {len(rows)} results. "
    body = " ".join(
        narrate_table_row(headers, row, index + 1) for index, row in enumerate(rows)
    )
    return intro + body


def narrate_table_row(headers: list[str], row: list[str], row_number: int) -> str:
    pairs = list(zip(headers, row))
    if not pairs:
        return ""

    first_header, first_value = pairs[0]
    label_header = first_header.casefold()

    if label_header in {"measure", "metric", "term", "marker", "item"}:
        leading = f"For {first_value}, "
        detail_pairs = pairs[1:]
    else:
        leading = f"Row {row_number}. "
        detail_pairs = pairs

    details = ", ".join(f"{header} {value}" for header, value in detail_pairs if value)
    if not details:
        return leading.strip() + "."
    return f"{leading}{details}."


def normalize_inline_markdown(text: str) -> str:
    normalized = text
    normalized = normalized.replace("<br>", " ")
    normalized = re.sub(r"`([^`]+)`", r"\1", normalized)
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", normalized)
    normalized = re.sub(r"\*\*([^*]+)\*\*", r"\1", normalized)
    normalized = re.sub(r"\*([^*]+)\*", r"\1", normalized)
    normalized = normalized.replace("—", ", ")
    normalized = normalized.replace("–", " to ")
    for raw_tag, spoken in TAG_REPLACEMENTS.items():
        normalized = normalized.replace(raw_tag, spoken)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def apply_pacing_breaks(text: str) -> str:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    if len(sentences) < 2:
        return text

    paced_parts: list[str] = [sentences[0]]
    previous_landing_sentence = False

    for index in range(1, len(sentences)):
        previous = sentences[index - 1]
        current = sentences[index]
        current_is_landing = is_long_sentence(previous) and is_short_sentence(current)
        if current_is_landing or previous_landing_sentence:
            paced_parts.append("\n\n" + current)
        else:
            paced_parts.append(" " + current)
        previous_landing_sentence = current_is_landing

    return "".join(paced_parts)


def apply_dramatic_pauses(text: str) -> str:
    for phrase in DRAMATIC_PAUSE_PHRASES:
        escaped = re.escape(phrase)
        text = re.sub(
            r"(?<=[.!?])\s+" + escaped,
            "\n\n" + phrase,
            text,
        )
        if text.startswith(phrase):
            text = "\n\n" + text
    return text.lstrip("\n")


def is_long_sentence(text: str) -> bool:
    words = len(text.split())
    return len(text) >= 140 or words >= 24


def is_short_sentence(text: str) -> bool:
    words = len(text.split())
    return len(text) <= 70 and words <= 12


def attach_first_use_notes(
    blocks: list[Block],
    entries: dict[str, GlossaryEntry],
    inline_notes: bool,
    max_notes_per_block: int = 2,
) -> None:
    seen_terms: set[str] = set()
    ordered_terms = sorted(
        entries.values(),
        key=lambda entry: (
            0 if entry.first_use_note or entry.pronunciation_note else 1,
            -len(entry.term),
            entry.term.casefold(),
        ),
    )

    for block in blocks:
        block.first_use_notes = []
        if not block.speech_text:
            block.tts_text = ""
            continue

        for entry in ordered_terms:
            if entry.term in seen_terms:
                continue
            if len(block.first_use_notes) >= max_notes_per_block:
                break
            if not text_contains_term(block.speech_text, entry.term):
                continue
            note = entry.first_use_note or default_first_use_note(entry)
            if not note:
                seen_terms.add(entry.term)
                continue
            block.first_use_notes.append(note)
            seen_terms.add(entry.term)

        if inline_notes and block.first_use_notes:
            prefix = " ".join(block.first_use_notes)
            block.tts_text = f"{prefix} {block.speech_text}".strip()
        else:
            block.tts_text = block.speech_text


def text_contains_term(text: str, term: str) -> bool:
    if not term:
        return False
    if re.fullmatch(r"[A-Za-z0-9]+", term):
        return bool(re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE))
    return term in text


def default_first_use_note(entry: GlossaryEntry) -> str | None:
    if entry.pronunciation_note and entry.spoken:
        return f"Term note: {entry.term} is pronounced {entry.spoken}."
    if entry.expansion and entry.spoken:
        return f"Term note: {entry.spoken} stands for {entry.expansion}."
    if entry.spoken and entry.spoken.lower() != entry.term.lower():
        return f"Term note: {entry.term} is pronounced {entry.spoken}."
    return None


def chunk_blocks(blocks: list[Block], max_chars: int) -> list[dict]:
    chunks: list[dict] = []
    current: list[Block] = []
    current_text = ""

    def flush() -> None:
        nonlocal current, current_text
        if not current:
            return
        chunk_id = len(chunks) + 1
        text = "\n\n".join(block.tts_text for block in current if block.tts_text).strip()
        if not text:
            current = []
            current_text = ""
            return
        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_start_line": current[0].source_start_line,
                "source_end_line": current[-1].source_end_line,
                "section_path": current[-1].section_path,
                "first_use_notes": [
                    note for block in current for note in block.first_use_notes
                ],
                "text": text,
            }
        )
        current = []
        current_text = ""

    for block in blocks:
        if not block.tts_text:
            continue
        candidate = block.tts_text if not current_text else f"{current_text}\n\n{block.tts_text}"
        if len(candidate) <= max_chars:
            current.append(block)
            current_text = candidate
            continue

        if current:
            flush()

        if len(block.tts_text) <= max_chars:
            current.append(block)
            current_text = block.tts_text
            continue

        for segment in split_long_text(block.tts_text, max_chars):
            chunks.append(
                {
                    "chunk_id": len(chunks) + 1,
                    "source_start_line": block.source_start_line,
                    "source_end_line": block.source_end_line,
                    "section_path": block.section_path,
                    "first_use_notes": block.first_use_notes,
                    "text": segment,
                }
            )

    flush()
    return chunks


def split_long_text(text: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    segments: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            segments.append(current)
        if len(sentence) <= max_chars:
            current = sentence
            continue
        segments.extend(
            sentence[index : index + max_chars]
            for index in range(0, len(sentence), max_chars)
        )
        current = ""

    if current:
        segments.append(current)

    return segments


def write_outputs(
    blocks: list[Block],
    glossary: dict[str, GlossaryEntry],
    chunks: list[dict],
    build_dir: Path,
    source_path: Path,
    voice: str,
    model: str,
    speed: float,
    instructions: str,
) -> None:
    build_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir = build_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    for stale_file in chunk_dir.glob("*.txt"):
        stale_file.unlink()

    narration_text = "\n\n".join(block.speech_text for block in blocks if block.speech_text)
    (build_dir / "narration.txt").write_text(narration_text + "\n", encoding="utf-8")

    serializable_blocks = [asdict(block) for block in blocks]
    (build_dir / "blocks.json").write_text(
        json.dumps(serializable_blocks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    serializable_glossary = {
        term: asdict(entry) for term, entry in sorted(glossary.items(), key=lambda item: item[0].casefold())
    }
    (build_dir / "lexicon.json").write_text(
        json.dumps(serializable_glossary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    for chunk in chunks:
        chunk_path = chunk_dir / f"{chunk['chunk_id']:04d}.txt"
        chunk_path.write_text(chunk["text"] + "\n", encoding="utf-8")

    (build_dir / "chunks.json").write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "source": str(source_path),
        "start_heading": START_HEADING,
        "end_heading": END_HEADING,
        "chunk_count": len(chunks),
        "defaults": {
            "model": model,
            "voice": voice,
            "speed": speed,
            "response_format": "wav",
            "instructions": instructions,
        },
    }
    (build_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build audiobook transcript artifacts in audiobook/build."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--front-matter", type=Path, default=DEFAULT_FRONT_MATTER)
    parser.add_argument("--max-chars", type=int, default=2200)
    parser.add_argument("--voice", default="nova")
    parser.add_argument("--model", default="gpt-4o-mini-tts")
    parser.add_argument("--speed", type=float, default=0.94)
    parser.add_argument(
        "--instructions",
        default=DEFAULT_TTS_INSTRUCTIONS,
    )
    parser.add_argument(
        "--suppress-inline-notes",
        action="store_true",
        help="Keep first-use notes in metadata only instead of folding them into TTS text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scoped_lines, start_line, end_line = extract_scope(load_lines(args.source))
    blocks = parse_blocks(scoped_lines)
    blocks, glossary = extract_glossary(blocks)
    glossary = apply_overrides(glossary, args.overrides)
    blocks = load_front_matter(args.front_matter) + blocks
    assign_sections(blocks)
    normalize_blocks(blocks)
    attach_first_use_notes(
        blocks,
        glossary,
        inline_notes=not args.suppress_inline_notes,
    )
    chunks = chunk_blocks(blocks, max_chars=args.max_chars)
    write_outputs(
        blocks=blocks,
        glossary=glossary,
        chunks=chunks,
        build_dir=args.build_dir,
        source_path=args.source,
        voice=args.voice,
        model=args.model,
        speed=args.speed,
        instructions=args.instructions,
    )
    print(
        f"Built audiobook artifacts from lines {start_line}-{end_line - 1} "
        f"into {args.build_dir} ({len(blocks)} blocks, {len(chunks)} chunks)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
