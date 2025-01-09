# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
from collections.abc import AsyncGenerator
from typing import Any, ClassVar, cast

from pydantic import BaseModel

from semantic_kernel.contents.audio_content import AudioContent


class AudioRecorderStream(BaseModel):
    """A class to record audio from the microphone and save it to a WAV file.

    To start recording, press the spacebar. To stop recording, release the spacebar.

    To use as a context manager, that automatically removes the output file after exiting the context:
    ```
    with AudioRecorder(output_filepath="output.wav") as recorder:
        recorder.start_recording()
        # Do something with the recorded audio
        ...
    ```
    """

    # Audio recording parameters
    CHANNELS: ClassVar[int] = 1
    SAMPLE_RATE: ClassVar[int] = 24000
    CHUNK_LENGTH_S: ClassVar[float] = 0.05
    device_id: int | None = None

    async def stream_audio_content(self) -> AsyncGenerator[AudioContent, None]:
        import sounddevice as sd  # type: ignore

        # device_info = sd.query_devices()
        # print(device_info)

        read_size = int(self.SAMPLE_RATE * 0.02)

        stream = sd.InputStream(
            channels=self.CHANNELS,
            samplerate=self.SAMPLE_RATE,
            dtype="int16",
            device=self.device_id,
        )
        stream.start()
        try:
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0)
                    continue

                data, _ = stream.read(read_size)
                yield AudioContent(data=base64.b64encode(cast(Any, data)), data_format="base64", mime_type="audio/wav")
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()
