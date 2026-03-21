from pathlib import Path
import unittest

from audiobook.build_audiobook import (
    DEFAULT_TTS_INSTRUCTIONS,
    GlossaryEntry,
    apply_dramatic_pauses,
    apply_pacing_breaks,
    attach_first_use_notes,
    extract_glossary,
    extract_scope,
    load_front_matter,
    normalize_blocks,
    normalize_table,
    parse_blocks,
)


class BuildAudiobookTests(unittest.TestCase):
    def test_extract_scope_stops_before_appendices(self) -> None:
        lines = [
            "# Title",
            "",
            "# Preface: How to Read This Book",
            "Preface text.",
            "# Epilogue: The Navigator",
            "Epilogue text.",
            "# Appendices",
            "Appendix text.",
        ]

        scoped, start_line, end_line = extract_scope(lines)

        self.assertEqual(start_line, 3)
        self.assertEqual(end_line, 7)
        self.assertEqual([line for _, line in scoped][-1], "Epilogue text.")

    def test_glossary_is_mined_but_not_emitted(self) -> None:
        scoped_lines = [
            (1, "# Preface: How to Read This Book"),
            (2, "Intro."),
            (3, "# Glossary of Key Terms"),
            (4, "**IIT.** Integrated Information Theory (Tononi)."),
            (5, ""),
            (6, "**Φ** (fye, rhymes 'eye'). The central quantity of IIT."),
            (7, "# PART ONE: THE PROBLEM AND THE METHOD"),
            (8, "Body text."),
        ]

        blocks = parse_blocks(scoped_lines)
        cleaned_blocks, glossary = extract_glossary(blocks)

        self.assertNotIn("Glossary of Key Terms", [block.heading_text for block in cleaned_blocks])
        self.assertIn("IIT", glossary)
        self.assertEqual(glossary["Φ"].spoken, "fye")

    def test_first_use_notes_can_be_folded_into_tts_text(self) -> None:
        blocks = parse_blocks(
            [
                (1, "# Chapter 1: Test"),
                (2, "IIT measures Φ in this paragraph."),
            ]
        )
        blocks, _ = extract_glossary(blocks)
        normalize_blocks(blocks)
        entries = {
            "IIT": GlossaryEntry(
                term="IIT",
                description="Integrated Information Theory.",
                spoken="I I T",
                expansion="Integrated Information Theory",
            ),
            "Φ": GlossaryEntry(
                term="Φ",
                description="Integrated information.",
                spoken="fye",
                pronunciation_note="fye, rhymes 'eye'",
            ),
        }

        attach_first_use_notes(blocks, entries, inline_notes=True)

        paragraph_block = next(block for block in blocks if block.kind == "paragraph")
        self.assertIn("Term note: I I T stands for Integrated Information Theory.", paragraph_block.tts_text)
        self.assertIn("Term note: Φ is pronounced fye.", paragraph_block.tts_text)

    def test_front_matter_is_loaded_as_prepended_blocks(self) -> None:
        path = Path("audiobook/front_matter.json")

        blocks = load_front_matter(path)

        self.assertEqual(blocks[0].kind, "heading")
        self.assertEqual(blocks[0].heading_text, "Dedication")
        self.assertEqual(blocks[1].kind, "paragraph")
        self.assertIn("every referenced researcher", blocks[1].text)

    def test_small_table_is_narrated_with_values(self) -> None:
        narrated = normalize_table(
            "\n".join(
                [
                    "| Measure | Value | 95% CI |",
                    "|---|---|---|",
                    "| Normalized advantage | +3.32% | [+0.87%, +5.77%] |",
                    "| Maze win rate | 53.3% | [43.1%, 63.3%] |",
                ]
            )
        )

        self.assertIn("For Normalized advantage, Value +3.32%", narrated)
        self.assertIn("95% CI [+0.87%, +5.77%]", narrated)
        self.assertIn("For Maze win rate, Value 53.3%", narrated)
        self.assertNotIn("companion text", narrated)

    def test_parse_blocks_keeps_full_markdown_table_together(self) -> None:
        blocks = parse_blocks(
            [
                (1, "| Measure | Value | 95% CI |"),
                (2, "|---|---|---|"),
                (3, "| Normalized advantage | +3.32% | [+0.87%, +5.77%] |"),
                (4, "| Maze win rate | 53.3% | [43.1%, 63.3%] |"),
            ]
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "table")
        self.assertEqual(len(blocks[0].text.splitlines()), 4)

    def test_pacing_breaks_isolate_short_landing_sentence(self) -> None:
        text = (
            "This is a deliberately long sentence that keeps stacking clause on "
            "clause so the cadence stretches out and the listener feels the weight "
            "of the idea before the point arrives. It matters. The next sentence "
            "returns to normal exposition."
        )

        paced = apply_pacing_breaks(text)

        self.assertIn("arrives.\n\nIt matters.\n\nThe next sentence", paced)

    def test_dramatic_pauses_insert_break_before_curated_phrases(self) -> None:
        text = (
            "Every morning you wake up and something happens that no theory "
            "in science can explain. The lights come on. Not the lights in "
            "your room, the lights of experience."
        )

        paced = apply_dramatic_pauses(text)

        self.assertIn("explain.\n\nThe lights come on.", paced)

    def test_dramatic_pauses_handle_first_sentence_phrase(self) -> None:
        text = "There is something it is like to hear a door slam."

        paced = apply_dramatic_pauses(text)

        self.assertEqual(paced, text)

    def test_default_instructions_include_term_note_and_heading_pause_guidance(self) -> None:
        self.assertIn("When a sentence begins with 'Term note:'", DEFAULT_TTS_INSTRUCTIONS)
        self.assertIn("When a long, dense sentence is followed by a short sentence", DEFAULT_TTS_INSTRUCTIONS)
        self.assertIn("Add a natural pause before and after chapter and part headings.", DEFAULT_TTS_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
