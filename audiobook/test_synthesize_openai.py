import tempfile
import unittest
import wave
from pathlib import Path

from audiobook.synthesize_openai import (
    build_mp3_transcode_command,
    format_headroom_filter,
    merge_audio_files,
)


def write_silent_wav(path: Path, frame_count: int = 8000) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b"\x00\x00" * frame_count)


class SynthesizeOpenAITests(unittest.TestCase):
    def test_format_headroom_filter_builds_volume_filter(self) -> None:
        self.assertEqual(format_headroom_filter(2.0), "volume=-2dB")
        self.assertEqual(format_headroom_filter(1.5), "volume=-1.5dB")
        self.assertIsNone(format_headroom_filter(0))

    def test_format_headroom_filter_rejects_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            format_headroom_filter(-0.5)

    def test_build_mp3_transcode_command_applies_headroom(self) -> None:
        command = build_mp3_transcode_command(
            ffmpeg_path="ffmpeg",
            master_path=Path("/tmp/master.wav"),
            mp3_path=Path("/tmp/final.mp3"),
            headroom_db=2.0,
        )

        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "/tmp/master.wav",
                "-af",
                "volume=-2dB",
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                "/tmp/final.mp3",
            ],
        )

    def test_merge_audio_files_builds_master_and_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_silent_wav(output_dir / "0001.wav")
            write_silent_wav(output_dir / "0002.wav")
            (output_dir / "concat.txt").write_text(
                "file '0001.wav'\nfile '0002.wav'\n",
                encoding="utf-8",
            )

            outputs = merge_audio_files(
                output_dir=output_dir,
                response_format="wav",
                final_basename="test_final",
                create_mp3=True,
                mp3_headroom_db=2.0,
            )

            self.assertTrue(Path(outputs["master"]).exists())
            self.assertTrue(Path(outputs["mp3"]).exists())
            self.assertGreater(Path(outputs["master"]).stat().st_size, 0)
            self.assertGreater(Path(outputs["mp3"]).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
