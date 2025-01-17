# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any, Final

import numpy as np
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack
from av.audio.frame import AudioFrame
from av.frame import Frame
from pydantic import Field, PrivateAttr
from sounddevice import InputStream, OutputStream

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

SAMPLE_RATE: Final[int] = 48000
TRACK_CHANNELS: Final[int] = 1
PLAYER_CHANNELS: Final[int] = 2
FRAME_DURATION: Final[int] = 20
DTYPE: Final[np.dtype] = np.int16


class SKAudioTrack(KernelBaseModel, MediaStreamTrack):
    """A simple class using sounddevice to record audio from the default input device.

    And implementing the MediaStreamTrack interface for use with aiortc.
    """

    kind: str = "audio"
    sample_rate: int = SAMPLE_RATE
    channels: int = TRACK_CHANNELS
    frame_duration: int = FRAME_DURATION
    dtype: np.dtype = DTYPE
    device: str | int | None = None
    queue: asyncio.Queue[Frame] = Field(default_factory=asyncio.Queue)
    is_recording: bool = False
    stream: InputStream | None = None
    frame_size: int = 0
    _recording_task: asyncio.Task | None = None
    _loop: asyncio.AbstractEventLoop | None = None
    _pts: int = 0  # Add this to track the pts

    def __init__(self, **kwargs: Any):
        """Initialize the audio track.

        Args:
            **kwargs: Additional keyword arguments.

        """
        kwargs["frame_size"] = int(
            kwargs.get("sample_rate", SAMPLE_RATE) * kwargs.get("frame_duration", FRAME_DURATION) / 1000
        )
        super().__init__(**kwargs)
        MediaStreamTrack.__init__(self)

    async def recv(self) -> Frame:
        """Receive the next frame of audio data."""
        if not self._recording_task:
            self._recording_task = asyncio.create_task(self.start_recording())

        try:
            return await self.queue.get()
        except Exception as e:
            logger.error(f"Error receiving audio frame: {e!s}")
            raise MediaStreamError("Failed to receive audio frame")

    async def start_recording(self):
        """Start recording audio from the input device."""
        if self.is_recording:
            return

        self.is_recording = True
        self._loop = asyncio.get_running_loop()
        self._pts = 0  # Reset pts when starting recording

        try:

            def callback(indata: np.ndarray, frames: int, time: Any, status: Any) -> None:
                if status:
                    logger.warning(f"Audio input status: {status}")

                audio_data = indata.copy()
                if audio_data.dtype != self.dtype:
                    if self.dtype == np.int16:
                        audio_data = (audio_data * 32767).astype(self.dtype)
                    else:
                        audio_data = audio_data.astype(self.dtype)

                frame = AudioFrame(
                    format="s16",
                    layout="mono",
                    samples=len(audio_data),
                )
                frame.rate = self.sample_rate
                frame.pts = self._pts
                frame.planes[0].update(audio_data.tobytes())
                self._pts += len(audio_data)
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.queue.put(frame), self._loop)

            self.stream = InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.frame_size,
                callback=callback,
            )
            self.stream.start()

            while self.is_recording:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in audio recording: {e!s}")
            raise
        finally:
            self.is_recording = False


class SKSimplePlayer(KernelBaseModel):
    """Simple class that plays audio using sounddevice.

    Make sure the device_id is set to the correct device for your system.

    The sample rate, channels and frame duration should be set to match the audio you
    are receiving, the defaults are for WebRTC.
    """

    device_id: int | None = None
    sample_rate: int = SAMPLE_RATE
    channels: int = PLAYER_CHANNELS
    frame_duration_ms: int = FRAME_DURATION
    queue: asyncio.Queue[np.ndarray] = Field(default_factory=asyncio.Queue)
    _stream: OutputStream | None = PrivateAttr(None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize the audio stream."""
        self._stream = OutputStream(
            callback=self.callback,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16,
            blocksize=int(self.sample_rate * self.frame_duration_ms / 1000),
            device=self.device_id,
        )

    async def __aenter__(self):
        """Start the audio stream when entering a context."""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Stop the audio stream when exiting a context."""
        self.stop()

    def start(self):
        """Start the audio stream."""
        if self._stream:
            self._stream.start()

    def stop(self):
        """Stop the audio stream."""
        if self._stream:
            self._stream.stop()

    def callback(self, outdata, frames, time, status):
        """This callback is called by sounddevice when it needs more audio data to play."""
        if status:
            logger.info(f"Audio output status: {status}")
        if self.queue.empty():
            return
        data: np.ndarray = self.queue.get_nowait()
        outdata[:] = data.reshape(outdata.shape)

    async def realtime_client_callback(self, frame: AudioFrame):
        """This function is used by the RealtimeClientBase to play audio."""
        await self.queue.put(frame.to_ndarray())

    async def add_audio(self, audio_content: AudioContent):
        """This function is used to add audio to the queue for playing.

        It uses a shortcut for this sample, because we know a AudioFrame is in the inner_content field.
        """
        if audio_content.inner_content and isinstance(audio_content.inner_content, AudioFrame):
            await self.queue.put(audio_content.inner_content.to_ndarray())
        # TODO (eavanvalkenburg): check ndarray
