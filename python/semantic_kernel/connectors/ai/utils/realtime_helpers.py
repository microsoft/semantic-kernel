# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, ClassVar, Final

import numpy as np
import numpy.typing as npt
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack
from av.audio.frame import AudioFrame
from av.frame import Frame
from pydantic import PrivateAttr
from sounddevice import InputStream, OutputStream

from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.events.realtime_event import AudioEvent
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

SAMPLE_RATE: Final[int] = 48000
TRACK_CHANNELS: Final[int] = 1
PLAYER_CHANNELS: Final[int] = 2
FRAME_DURATION: Final[int] = 20
DTYPE: Final[npt.DTypeLike] = np.int16


class SKAudioTrack(KernelBaseModel, MediaStreamTrack):
    """A simple class that implements the WebRTC MediaStreamTrack for audio from sounddevice."""

    kind: ClassVar[str] = "audio"
    device: str | int | None = None
    sample_rate: int = SAMPLE_RATE
    channels: int = TRACK_CHANNELS
    frame_duration: int = FRAME_DURATION
    dtype: npt.DTypeLike = DTYPE
    frame_size: int = 0
    _queue: asyncio.Queue[Frame] = PrivateAttr(default_factory=asyncio.Queue)
    _is_recording: bool = False
    _stream: InputStream | None = None
    _recording_task: asyncio.Task | None = None
    _loop: asyncio.AbstractEventLoop | None = None
    _pts: int = 0

    def __init__(
        self,
        *,
        device: str | int | None = None,
        sample_rate: int = SAMPLE_RATE,
        channels: int = TRACK_CHANNELS,
        frame_duration: int = FRAME_DURATION,
        dtype: npt.DTypeLike = DTYPE,
    ):
        """A simple class that implements the WebRTC MediaStreamTrack for audio from sounddevice.

        Make sure the device is set to the correct device for your system.

        Args:
            device: The device id to use for recording audio.
            sample_rate: The sample rate for the audio.
            channels: The number of channels for the audio.
            frame_duration: The duration of each audio frame in milliseconds.
            dtype: The data type for the audio.
            **kwargs: Additional keyword arguments.
        """
        args = {
            "device": device,
            "sample_rate": sample_rate,
            "channels": channels,
            "frame_duration": frame_duration,
            "dtype": dtype,
        }
        args["frame_size"] = int(
            args.get("sample_rate", SAMPLE_RATE) * args.get("frame_duration", FRAME_DURATION) / 1000
        )
        super().__init__(**args)
        MediaStreamTrack.__init__(self)

    async def recv(self) -> Frame:
        """Receive the next frame of audio data."""
        if not self._recording_task:
            self._recording_task = asyncio.create_task(self.start_recording())

        try:
            frame = await self._queue.get()
            self._queue.task_done()
            return frame
        except Exception as e:
            logger.error(f"Error receiving audio frame: {e!s}")
            raise MediaStreamError("Failed to receive audio frame")

    @asynccontextmanager
    async def stream_to_realtime_client(self, realtime_client: RealtimeClientBase):
        """Stream audio data to a RealtimeClientBase."""
        while True:
            frame = await self.recv()
            await realtime_client.send(AudioEvent(audio=AudioContent(data=frame.to_ndarray(), data_format="np.int16")))
            yield
            await asyncio.sleep(0.01)

    def _sounddevice_callback(self, indata: np.ndarray, frames: int, time: Any, status: Any) -> None:
        if status:
            logger.warning(f"Audio input status: {status}")
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._queue.put(self._create_frame(indata)), self._loop)

    def _create_frame(self, indata: np.ndarray) -> Frame:
        audio_data = indata.copy()
        if audio_data.dtype != self.dtype:
            audio_data = (
                (audio_data * 32767).astype(self.dtype) if self.dtype == np.int16 else audio_data.astype(self.dtype)
            )
        frame = AudioFrame(
            format="s16",
            layout="mono",
            samples=len(audio_data),
        )
        frame.rate = self.sample_rate
        frame.pts = self._pts
        frame.planes[0].update(audio_data.tobytes())
        self._pts += len(audio_data)
        return frame

    async def start_recording(self):
        """Start recording audio from the input device."""
        if self._is_recording:
            return

        self._is_recording = True
        self._loop = asyncio.get_running_loop()
        self._pts = 0  # Reset pts when starting recording

        try:
            self._stream = InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.frame_size,
                callback=self._sounddevice_callback,
            )
            self._stream.start()

            while self._is_recording:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in audio recording: {e!s}")
            raise
        finally:
            self._is_recording = False


class SKAudioPlayer(KernelBaseModel):
    """Simple class that plays audio using sounddevice.

    Make sure the device_id is set to the correct device for your system.

    The sample rate, channels and frame duration
    should be set to match the audio you
    are receiving.

    Args:
        device: The device id to use for playing audio.
        sample_rate: The sample rate for the audio.
        channels: The number of channels for the audio.
        dtype: The data type for the audio.
        frame_duration: The duration of each audio frame in milliseconds

    """

    device: int | None = None
    sample_rate: int = SAMPLE_RATE
    channels: int = PLAYER_CHANNELS
    dtype: npt.DTypeLike = DTYPE
    frame_duration: int = FRAME_DURATION
    _queue: asyncio.Queue[np.ndarray] | None = PrivateAttr(default=None)
    _stream: OutputStream | None = PrivateAttr(default=None)

    async def __aenter__(self):
        """Start the audio stream when entering a context."""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Stop the audio stream when exiting a context."""
        self.stop()

    def start(self):
        """Start the audio stream."""
        self._queue = asyncio.Queue()
        self._stream = OutputStream(
            callback=self._sounddevice_callback,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=int(self.sample_rate * self.frame_duration / 1000),
            device=self.device,
        )
        if self._stream and self._queue:
            self._stream.start()

    def stop(self):
        """Stop the audio stream."""
        if self._stream:
            self._stream.stop()
        self._stream = None
        self._queue = None

    def _sounddevice_callback(self, outdata, frames, time, status):
        """This callback is called by sounddevice when it needs more audio data to play."""
        if status:
            logger.info(f"Audio output status: {status}")
        if self._queue:
            if self._queue.empty():
                return
            data: np.ndarray = self._queue.get_nowait()
            if data.size == frames:
                outdata[:] = data.reshape(outdata.shape)
                self._queue.task_done()
            else:
                if data.size > frames:
                    self._queue.put_nowait(data[frames:])
                    outdata[:] = np.concatenate((np.empty(0, dtype=np.int16), data[:frames])).reshape(outdata.shape)
                else:
                    outdata[:] = np.concatenate((data, np.zeros(frames - len(data), dtype=np.int16))).reshape(
                        outdata.shape
                    )
                self._queue.task_done()

    async def client_callback(self, content: np.ndarray):
        """This function can be passed to the audio_output_callback field of the RealtimeClientBase."""
        if self._queue:
            await self._queue.put(content)
        else:
            logger.error(
                "Audio queue not initialized, make sure to call start before "
                "using the player, or use the context manager."
            )

    async def add_audio(self, audio_content: AudioContent) -> None:
        """This function is used to add audio to the queue for playing.

        It first checks if there is a AudioFrame in the inner_content of the AudioContent.
        If not, it checks if the data is a numpy array, bytes, or a string and converts it to a numpy array.
        """
        if not self._queue:
            logger.error(
                "Audio queue not initialized, make sure to call start before "
                "using the player, or use the context manager."
            )
            return
        if audio_content.inner_content and isinstance(audio_content.inner_content, AudioFrame):
            await self._queue.put(audio_content.inner_content.to_ndarray())
            return
        if isinstance(audio_content.data, np.ndarray):
            await self._queue.put(audio_content.data)
            return
        if isinstance(audio_content.data, bytes):
            await self._queue.put(np.frombuffer(audio_content.data, dtype=self.dtype))
            return
        if isinstance(audio_content.data, str):
            await self._queue.put(np.frombuffer(audio_content.data.encode(), dtype=self.dtype))
            return
        logger.error(f"Unknown audio content: {audio_content}")
