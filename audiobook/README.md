# Audiobook Pipeline

This folder contains an audiobook-only pipeline for turning `../book_v2.md`
into OpenAI-ready speech chunks without changing the rest of the repository.

## Design choices

- All code, configs, and generated artifacts stay inside `audiobook/`.
- The source glossary is mined for pronunciations and first-use notes, but the
  glossary is not narrated as a front-loaded appendix.
- First-use notes are introduced inline when terms actually appear.
- OpenAI synthesis is a second step that reads prepared chunks and writes audio
  files locally under `audiobook/audio/`.

## Files

- `build_audiobook.py`: extracts `Preface -> Epilogue`, normalizes markdown into
  spoken blocks, suppresses the standalone glossary, and emits chunked TTS input.
- `front_matter.json`: audiobook-local intro material that gets prepended before
  the Preface. This is where the dedication lives.
- `synthesize_openai.py`: reads prepared chunks and calls the OpenAI
  `audio/speech` endpoint.
- `lexicon_overrides.json`: audiobook-local pronunciation and first-use note
  overrides.
- `test_build_audiobook.py`: focused tests for boundary extraction, glossary
  mining, and first-use notes.

## Usage

Build the transcript and TTS chunks:

```bash
python3 audiobook/build_audiobook.py
```

Run the local tests:

```bash
python3 -m unittest audiobook/test_build_audiobook.py
```

Synthesize audio with OpenAI using the prepared chunks:

```bash
OPENAI_API_KEY=... python3 audiobook/synthesize_openai.py
```

The default synthesis flow now:

1. renders chunk WAV files under `audiobook/audio/`,
2. stitches them into `audiobook/audio/final_audiobook.wav`, and
3. transcodes that master to `audiobook/audio/final_audiobook.mp3`.

## Output layout

- `build/manifest.json`: build metadata and default synthesis settings.
- `build/blocks.json`: normalized narration blocks with source spans.
- `build/chunks.json`: chunked TTS payloads with optional inline first-use notes.
- `build/narration.txt`: full audiobook narration text.
- `build/chunks/*.txt`: one text file per prepared chunk.
- `audio/*.wav`: synthesized chunk audio and stitched WAV master.
- `audio/final_audiobook.mp3`: delivery encode built from the stitched WAV master.

## Inline terminology

The builder keeps the glossary out of the narrated flow. Instead it:

1. mines glossary entries and audiobook-local overrides,
2. tracks first use of terms in the actual narration,
3. attaches brief notes such as pronunciation hints or acronym expansions, and
4. optionally folds those notes into the TTS text.

That gives us the "introduce terms as they come" behavior without front-loading
an appendix before Chapter 1.

## Dedication

The dedication is stored in `front_matter.json`, so we can change audiobook-only
opening material without editing the manuscript.
