# Copyright (c) Microsoft. All rights reserved.

import io
import wave
from typing import ClassVar

import pyaudio

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.kernel_pydantic import KernelBaseModel


class AudioPlayer(KernelBaseModel):
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

                # Split the text into chunks based on the lenght of the data frames
                # so that the text is displayed at the same rate as the audio is played
                text_chunk_size_per_frame = max(1, len(text) / len(data_frames))
                for i, data in enumerate(data_frames):
                    stream.write(data)
                    print(text[i * text_chunk_size_per_frame : (i + 1) * text_chunk_size_per_frame], end="", flush=True)
            else:
                data = wf.readframes(self.CHUNK)
                while data:
                    stream.write(data)
                    data = wf.readframes(self.CHUNK)

            stream.stop_stream()
            stream.close()
            audio.terminate()
