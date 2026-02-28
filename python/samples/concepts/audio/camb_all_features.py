# Copyright (c) Microsoft. All rights reserved.

"""All-encompassing example of camb.ai integration with Semantic Kernel.

Demonstrates all 8 camb.ai features:
  1. Text-to-Speech (TTS) via CambTextToAudio service
  2. List Voices via CambPlugin
  3. Translation via CambPlugin
  4. Transcription (STT) via CambAudioToText service
  5. Translated TTS via CambPlugin
  6. Voice Cloning via CambPlugin
  7. Text-to-Sound via CambPlugin
  8. Audio Separation via CambPlugin

Requires:
    - CAMB_API_KEY in a .env file at the repo root or in environment
    - An audio sample clip (defaults to sabrina-original-clip.mp3)
    - pip install semantic-kernel[camb]

Usage:
    cd python
    source .venv/bin/activate
    python samples/concepts/audio/camb_all_features.py
"""

import asyncio
import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root
_repo_root = Path(__file__).resolve().parents[4]
load_dotenv(_repo_root / ".env")

from semantic_kernel.connectors.ai.camb import (
    CambAudioToText,
    CambAudioToTextExecutionSettings,
    CambPlugin,
    CambTextToAudio,
    CambTextToAudioExecutionSettings,
)
from semantic_kernel.contents.audio_content import AudioContent

API_KEY = os.environ.get("CAMB_API_KEY")
if not API_KEY:
    raise RuntimeError("Set CAMB_API_KEY in .env or environment")

_DEFAULT_SAMPLE = _repo_root.parent / "yt-dlp" / "voices" / "original" / "sabrina-original-clip.mp3"
AUDIO_SAMPLE = os.environ.get("CAMB_AUDIO_SAMPLE", str(_DEFAULT_SAMPLE))
if not Path(AUDIO_SAMPLE).exists():
    raise RuntimeError(f"Audio sample not found at {AUDIO_SAMPLE}")


def play(path: str) -> None:
    """Play audio with afplay (macOS)."""
    if sys.platform == "darwin":
        print(f"  Playing: {path}")
        subprocess.run(["afplay", path], check=False)
    else:
        print(f"  Audio saved at: {path}")


def save_and_play(data: bytes, suffix: str = ".wav") -> str:
    """Save audio bytes to a temp file and play."""
    path = tempfile.mktemp(suffix=suffix)
    with open(path, "wb") as f:
        f.write(data)
    play(path)
    return path


def save_and_play_b64(audio_b64: str, suffix: str = ".wav") -> str:
    """Decode base64 audio, save to temp file, and play."""
    data = base64.b64decode(audio_b64)
    return save_and_play(data, suffix)


# ---------------------------------------------------------------------------
# 1. Text-to-Speech via CambTextToAudio service
# ---------------------------------------------------------------------------
async def example_tts() -> None:
    """1. Text-to-Speech: convert text to audio using the SK service interface."""
    tts = CambTextToAudio(api_key=API_KEY)
    settings = CambTextToAudioExecutionSettings(
        voice_id=147320,
        language="en-us",
        output_format="wav",
    )

    results = await tts.get_audio_contents(
        "Hello from Semantic Kernel! This is a test of the camb dot A I text to speech integration.",
        settings=settings,
    )

    audio = results[0]
    print(f"  Audio: {len(audio.data)} bytes, mime_type={audio.mime_type}, model={audio.ai_model_id}")
    save_and_play(audio.data)


# ---------------------------------------------------------------------------
# 2. List Voices via CambPlugin
# ---------------------------------------------------------------------------
async def example_list_voices() -> None:
    """2. List Voices: show available voices from camb.ai."""
    import json

    plugin = CambPlugin(api_key=API_KEY)
    result = await plugin.list_voices()
    voices = json.loads(result)
    print(f"  Found {len(voices)} voices")
    for v in voices[:5]:
        print(f"    - {v['name']} (id={v['id']}, gender={v['gender']})")


# ---------------------------------------------------------------------------
# 3. Translation via CambPlugin
# ---------------------------------------------------------------------------
async def example_translation() -> None:
    """3. Translation: translate text between languages."""
    plugin = CambPlugin(api_key=API_KEY)

    # English (1) -> Spanish (2)
    result = await plugin.translate(
        text="Hello! How are you today? Semantic Kernel is great.",
        source_language=1,
        target_language=2,
    )
    print(f"  English -> Spanish: {result}")


# ---------------------------------------------------------------------------
# 4. Transcription (STT) via CambAudioToText service
# ---------------------------------------------------------------------------
async def example_transcription() -> None:
    """4. Transcription: transcribe audio to text using the SK service interface."""
    stt = CambAudioToText(api_key=API_KEY)
    settings = CambAudioToTextExecutionSettings(language=1)  # 1 = English
    audio_content = AudioContent(uri=AUDIO_SAMPLE)

    print(f"  Transcribing {Path(AUDIO_SAMPLE).name}... (this may take a minute)")
    results = await stt.get_text_contents(audio_content, settings=settings)

    text = results[0].text
    print(f"  Transcription: {text[:200]}{'...' if len(text) > 200 else ''}")


# ---------------------------------------------------------------------------
# 5. Translated TTS via CambPlugin
# ---------------------------------------------------------------------------
async def example_translated_tts() -> None:
    """5. Translated TTS: translate and speak in one step."""
    import json

    plugin = CambPlugin(api_key=API_KEY)

    result = await plugin.translated_tts(
        text="Hello, how are you doing today?",
        source_language=1,  # English
        target_language=76,  # French
        voice_id=147320,
    )

    parsed = json.loads(result)
    print(f"  Run ID: {parsed['run_id']}")
    print(f"  Content type: {parsed['content_type']}")
    save_and_play_b64(parsed["audio_base64"])


# ---------------------------------------------------------------------------
# 6. Voice Cloning via CambPlugin
# ---------------------------------------------------------------------------
async def example_clone_voice() -> None:
    """6. Voice Clone: clone a voice from audio sample and speak with it."""
    import json

    plugin = CambPlugin(api_key=API_KEY)

    # Clone the voice
    clone_result = await plugin.clone_voice(
        voice_name="sk_test_sabrina",
        audio_file_path=AUDIO_SAMPLE,
        gender=2,  # female
    )
    parsed = json.loads(clone_result)
    voice_id = parsed["voice_id"]
    print(f"  Cloned voice ID: {voice_id}, name: {parsed['voice_name']}")

    # Speak with the cloned voice using the TTS service
    tts = CambTextToAudio(api_key=API_KEY)
    settings = CambTextToAudioExecutionSettings(
        voice_id=voice_id,
        language="en-us",
        output_format="wav",
    )

    results = await tts.get_audio_contents(
        "Hello! This is a cloned voice speaking through Semantic Kernel and camb dot A I.",
        settings=settings,
    )
    print("  Speaking with cloned voice...")
    save_and_play(results[0].data)


# ---------------------------------------------------------------------------
# 7. Text-to-Sound via CambPlugin
# ---------------------------------------------------------------------------
async def example_text_to_sound() -> None:
    """7. Text-to-Sound: generate sound effects from a text description."""
    import json

    plugin = CambPlugin(api_key=API_KEY)

    result = await plugin.text_to_sound(prompt="gentle rain on a rooftop with distant thunder")

    parsed = json.loads(result)
    print(f"  Run ID: {parsed['run_id']}")
    print(f"  Audio length: {len(parsed['audio_base64'])} chars (base64)")
    save_and_play_b64(parsed["audio_base64"])


# ---------------------------------------------------------------------------
# 8. Audio Separation via CambPlugin
# ---------------------------------------------------------------------------
async def example_audio_separation() -> None:
    """8. Audio Separation: separate vocals from background in audio."""
    import json

    plugin = CambPlugin(api_key=API_KEY)

    print(f"  Separating {Path(AUDIO_SAMPLE).name}... (this may take a minute)")
    result = await plugin.separate_audio(audio_file_path=AUDIO_SAMPLE)

    parsed = json.loads(result)
    print(f"  Run ID: {parsed['run_id']}")
    print(f"  Vocals URL: {parsed['vocals_url']}")
    print(f"  Background URL: {parsed['background_url']}")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
async def main() -> None:
    examples = [
        example_tts,
        example_list_voices,
        example_translation,
        example_transcription,
        example_translated_tts,
        example_clone_voice,
        example_text_to_sound,
        example_audio_separation,
    ]

    for fn in examples:
        print(f"\n--- {fn.__doc__} ---")
        try:
            await fn()
            print("  PASSED")
        except Exception as e:
            print(f"  FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
