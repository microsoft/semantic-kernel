# Copyright (c) Microsoft. All rights reserved.

import io
import logging
import wave
from typing import ClassVar

import pyaudio
from pydantic import BaseModel

from semantic_kernel.contents import AudioContent

logging.basicConfig(level=logging.WARNING)
logger: logging.Logger = logging.getLogger(__name__)


class AudioPlayer(BaseModel):
    """A class to play an audio file to the default audio output device."""

    # Audio replay parameters
    CHUNK: ClassVar[int] = 1024

    audio_content: AudioContent

    def play(self, text: str | None = None) -> None:
        """Play the audio content to the default audio output device.

        Args:
            text (str, optional): The text to display while playing the audio. Defaults to None.
        """
        audio_stream = io.BytesIO(self.audio_content.data)
        with wave.open(audio_stream, "rb") as wf:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            if text:
                # Simulate the output of text while playing the audio
                data_frames = []

                data = wf.readframes(self.CHUNK)
                while data:
                    data_frames.append(data)
                    data = wf.readframes(self.CHUNK)

                if len(data_frames) < len(text):
                    logger.warning(
                        "The audio is too short to play the entire text. ",
                        "The text will be displayed without synchronization.",
                    )
                    print(text)
                else:
                    for data_frame, text_frame in self._zip_text_and_audio(text, data_frames):
                        stream.write(data_frame)
                        print(text_frame, end="", flush=True)
                    print()
            else:
                data = wf.readframes(self.CHUNK)
                while data:
                    stream.write(data)
                    data = wf.readframes(self.CHUNK)

            stream.stop_stream()
            stream.close()
            audio.terminate()

    def _zip_text_and_audio(self, text: str, audio_frames: list) -> zip:
        """Zip the text and audio frames together so that they can be displayed in sync.

        This is done by evenly distributing empty strings between each character and
        append the remaining empty strings at the end.

        Args:
            text (str): The text to display while playing the audio.
            audio_frames (list): The audio frames to play.

        Returns:
            zip: The zipped text and audio frames.
        """
        text_frames = list(text)
        empty_string_count = len(audio_frames) - len(text_frames)
        empty_string_spacing = len(text_frames) // empty_string_count

        modified_text_frames = []
        current_empty_string_count = 0
        for i, text_frame in enumerate(text_frames):
            modified_text_frames.append(text_frame)
            if current_empty_string_count < empty_string_count and i % empty_string_spacing == 0:
                modified_text_frames.append("")
                current_empty_string_count += 1

        if current_empty_string_count < empty_string_count:
            modified_text_frames.extend([""] * (empty_string_count - current_empty_string_count))

        return zip(audio_frames, modified_text_frames)
