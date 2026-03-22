#!/usr/bin/env python3
"""Synthesize prepared audiobook chunks with the OpenAI audio/speech API."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BUILD_DIR = SCRIPT_DIR / "build"
DEFAULT_AUDIO_DIR = SCRIPT_DIR / "audio"
API_URL = "https://api.openai.com/v1/audio/speech"
DEFAULT_MP3_HEADROOM_DB = 2.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize audiobook chunks with the OpenAI speech API."
    )
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--model")
    parser.add_argument("--voice")
    parser.add_argument("--speed", type=float)
    parser.add_argument("--response-format")
    parser.add_argument("--instructions")
    parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Leave chunk audio files as-is and do not assemble final audiobook files.",
    )
    parser.add_argument(
        "--skip-mp3",
        action="store_true",
        help="Build the stitched master file only and skip MP3 delivery encoding.",
    )
    parser.add_argument(
        "--final-basename",
        default="final_audiobook",
        help="Base filename for the stitched master and delivery files.",
    )
    parser.add_argument(
        "--mp3-headroom-db",
        type=float,
        default=DEFAULT_MP3_HEADROOM_DB,
        help=(
            "Reduce the stitched master by this many dB before MP3 encoding. "
            "This leaves codec headroom and helps avoid delivery clipping."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only synthesize the first N chunks. Zero means all chunks.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Rebuild audio files even if they already exist.",
    )
    return parser.parse_args()


def load_manifest(build_dir: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads((build_dir / "manifest.json").read_text(encoding="utf-8"))
    chunks = json.loads((build_dir / "chunks.json").read_text(encoding="utf-8"))
    return manifest, chunks


def resolve_settings(manifest: dict, args: argparse.Namespace) -> dict:
    defaults = manifest["defaults"]
    return {
        "model": args.model or defaults["model"],
        "voice": args.voice or defaults["voice"],
        "speed": args.speed if args.speed is not None else defaults["speed"],
        "response_format": args.response_format or defaults["response_format"],
        "instructions": args.instructions or defaults["instructions"],
    }


def synthesize_chunk(
    text: str,
    output_path: Path,
    settings: dict,
    api_key: str,
) -> None:
    payload = {
        "model": settings["model"],
        "voice": settings["voice"],
        "input": text,
        "response_format": settings["response_format"],
        "speed": settings["speed"],
        "instructions": settings["instructions"],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            output_path.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI speech request failed for {output_path.name}: {exc.code} {body}"
        ) from exc


def require_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg is required for final merge, but it was not found on PATH.")
    return ffmpeg_path


def run_ffmpeg(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "ffmpeg command failed:\n"
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )


def format_headroom_filter(headroom_db: float) -> str | None:
    if headroom_db < 0:
        raise ValueError("MP3 headroom must be zero or positive.")
    if headroom_db == 0:
        return None
    return f"volume=-{headroom_db:g}dB"


def build_mp3_transcode_command(
    *,
    ffmpeg_path: str,
    master_path: Path,
    mp3_path: Path,
    headroom_db: float,
) -> list[str]:
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(master_path),
    ]
    headroom_filter = format_headroom_filter(headroom_db)
    if headroom_filter:
        command.extend(["-af", headroom_filter])
    command.extend(
        [
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path),
        ]
    )
    return command


def merge_audio_files(
    output_dir: Path,
    response_format: str,
    final_basename: str,
    create_mp3: bool,
    mp3_headroom_db: float,
) -> dict[str, str]:
    ffmpeg_path = require_ffmpeg()
    concat_path = output_dir / "concat.txt"
    master_path = output_dir / f"{final_basename}.{response_format}"

    run_ffmpeg(
        [
            ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(master_path),
        ]
    )

    outputs = {"master": str(master_path)}

    if create_mp3 and response_format != "mp3":
        mp3_path = output_dir / f"{final_basename}.mp3"
        run_ffmpeg(
            build_mp3_transcode_command(
                ffmpeg_path=ffmpeg_path,
                master_path=master_path,
                mp3_path=mp3_path,
                headroom_db=mp3_headroom_db,
            )
        )
        outputs["mp3"] = str(mp3_path)

    return outputs


def main() -> int:
    args = parse_args()
    manifest, chunks = load_manifest(args.build_dir)
    settings = resolve_settings(manifest, args)
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(
            f"Missing API key. Set {args.api_key_env} before running synthesis.",
            file=sys.stderr,
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    selected_chunks = chunks[: args.limit] if args.limit else chunks
    concat_entries: list[str] = []

    for chunk in selected_chunks:
        output_path = args.output_dir / f"{chunk['chunk_id']:04d}.{settings['response_format']}"
        concat_entries.append(f"file '{output_path.name}'")
        if output_path.exists() and not args.overwrite:
            print(f"Skipping existing {output_path.name}")
            continue
        print(f"Synthesizing {output_path.name}")
        synthesize_chunk(
            text=chunk["text"],
            output_path=output_path,
            settings=settings,
            api_key=api_key,
        )

    (args.output_dir / "concat.txt").write_text(
        "\n".join(concat_entries) + ("\n" if concat_entries else ""),
        encoding="utf-8",
    )
    (args.output_dir / "synthesis_settings.json").write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    merged_outputs: dict[str, str] = {}
    if not args.skip_merge and selected_chunks:
        merged_outputs = merge_audio_files(
            output_dir=args.output_dir,
            response_format=settings["response_format"],
            final_basename=args.final_basename,
            create_mp3=not args.skip_mp3,
            mp3_headroom_db=args.mp3_headroom_db,
        )

    print(f"Wrote audio chunks to {args.output_dir}")
    if merged_outputs:
        print(json.dumps(merged_outputs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
