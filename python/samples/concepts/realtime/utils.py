# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import logging
import threading
from typing import Any, ClassVar, Final, cast

import numpy as np
import numpy.typing as npt
import sounddevice as sd
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack
from av.audio.frame import AudioFrame
from av.frame import Frame
from pydantic import BaseModel, ConfigDict, PrivateAttr
from sounddevice import InputStream, OutputStream

from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents import AudioContent, RealtimeAudioEvent

logger = logging.getLogger(__name__)

SAMPLE_RATE: Final[int] = 24000
RECORDER_CHANNELS: Final[int] = 1
PLAYER_CHANNELS: Final[int] = 1
FRAME_DURATION: Final[int] = 100
SAMPLE_RATE_WEBRTC: Final[int] = 48000
RECORDER_CHANNELS_WEBRTC: Final[int] = 1
PLAYER_CHANNELS_WEBRTC: Final[int] = 2
FRAME_DURATION_WEBRTC: Final[int] = 20
DTYPE: Final[npt.DTypeLike] = np.int16


def check_audio_devices():
    logger.info(sd.query_devices())


# region: Recorders


class AudioRecorderWebRTC(BaseModel, MediaStreamTrack):
    """A simple class that implements the WebRTC MediaStreamTrack for audio from sounddevice.

    This class is meant as a demo sample and is not meant for production use.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)

    kind: ClassVar[str] = "audio"
    device: str | int | None = None
    sample_rate: int
    channels: int
    frame_duration: int
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
        sample_rate: int = SAMPLE_RATE_WEBRTC,
        channels: int = RECORDER_CHANNELS_WEBRTC,
        frame_duration: int = FRAME_DURATION_WEBRTC,
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
        """
        super().__init__(**{
            "device": device,
            "sample_rate": sample_rate,
            "channels": channels,
            "frame_duration": frame_duration,
            "dtype": dtype,
            "frame_size": int(sample_rate * frame_duration / 1000),
        })
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
        except asyncio.CancelledError:
            logger.debug("Recording task was stopped.")
        except KeyboardInterrupt:
            logger.debug("Recording task was stopped.")
        except Exception as e:
            logger.error(f"Error in audio recording: {e!s}")
            raise
        finally:
            self._is_recording = False


class AudioRecorderWebsocket(BaseModel):
    """A simple class that implements a sounddevice for use with websockets.

    This class is meant as a demo sample and is not meant for production use.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)

    realtime_client: RealtimeClientBase
    device: str | int | None = None
    sample_rate: int
    channels: int
    frame_duration: int
    dtype: npt.DTypeLike = DTYPE
    frame_size: int = 0
    _stream: InputStream | None = None
    _pts: int = 0
    _stream_task: asyncio.Task | None = None

    def __init__(
        self,
        *,
        realtime_client: RealtimeClientBase,
        device: str | int | None = None,
        sample_rate: int = SAMPLE_RATE,
        channels: int = RECORDER_CHANNELS,
        frame_duration: int = FRAME_DURATION,
        dtype: npt.DTypeLike = DTYPE,
    ):
        """A simple class that implements the WebRTC MediaStreamTrack for audio from sounddevice.

        Make sure the device is set to the correct device for your system.

        Args:
            realtime_client: The RealtimeClientBase to use for streaming audio.
            device: The device id to use for recording audio.
            sample_rate: The sample rate for the audio.
            channels: The number of channels for the audio.
            frame_duration: The duration of each audio frame in milliseconds.
            dtype: The data type for the audio.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**{
            "realtime_client": realtime_client,
            "device": device,
            "sample_rate": sample_rate,
            "channels": channels,
            "frame_duration": frame_duration,
            "dtype": dtype,
            "frame_size": int(sample_rate * frame_duration / 1000),
        })

    async def __aenter__(self):
        """Stream audio data to a RealtimeClientBase."""
        if not self._stream_task:
            self._stream_task = asyncio.create_task(self._start_stream())
        return self

    async def _start_stream(self):
        self._pts = 0  # Reset pts when starting recording
        self._stream = InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=self.dtype,
            blocksize=self.frame_size,
        )
        self._stream.start()
        try:
            while True:
                if self._stream.read_available < self.frame_size:
                    await asyncio.sleep(0)
                    continue
                data, _ = self._stream.read(self.frame_size)

                await self.realtime_client.send(
                    RealtimeAudioEvent(audio=AudioContent(data=base64.b64encode(cast(Any, data)).decode("utf-8")))
                )

                await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass

    async def __aexit__(self, exc_type, exc, tb):
        """Stop recording audio."""
        if self._stream_task:
            self._stream_task.cancel()
            await self._stream_task
        if self._stream:
            self._stream.stop()
            self._stream.close()


# region: Players


class AudioPlayerWebRTC(BaseModel):
    """Simple class that plays audio using sounddevice.

    This class is meant as a demo sample and is not meant for production use.

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

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)

    device: int | None = None
    sample_rate: int = SAMPLE_RATE_WEBRTC
    channels: int = PLAYER_CHANNELS_WEBRTC
    dtype: npt.DTypeLike = DTYPE
    frame_duration: int = FRAME_DURATION_WEBRTC
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
            logger.debug(f"Audio output status: {status}")
        if self._queue:
            if self._queue.empty():
                return
            data = self._queue.get_nowait()
            outdata[:] = data.reshape(outdata.shape)
            self._queue.task_done()
        else:
            logger.error(
                "Audio queue not initialized, make sure to call start before "
                "using the player, or use the context manager."
            )

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


class AudioPlayerWebsocket(BaseModel):
    """Simple class that plays audio using sounddevice.

    This class is meant as a demo sample and is not meant for production use.

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

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)

    device: int | None = None
    sample_rate: int = SAMPLE_RATE
    channels: int = PLAYER_CHANNELS
    dtype: npt.DTypeLike = DTYPE
    frame_duration: int = FRAME_DURATION
    _lock: Any = PrivateAttr(default_factory=threading.Lock)
    _queue: list[np.ndarray] = PrivateAttr(default_factory=list)
    _stream: OutputStream | None = PrivateAttr(default=None)
    _frame_count: int = 0

    async def __aenter__(self):
        """Start the audio stream when entering a context."""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Stop the audio stream when exiting a context."""
        self.stop()

    def start(self):
        """Start the audio stream."""
        with self._lock:
            self._queue = []
        self._stream = OutputStream(
            callback=self._sounddevice_callback,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=int(self.sample_rate * self.frame_duration / 1000),
            device=self.device,
        )
        if self._stream:
            self._stream.start()

    def stop(self):
        """Stop the audio stream."""
        if self._stream:
            self._stream.stop()
        self._stream = None
        with self._lock:
            self._queue = []

    def _sounddevice_callback(self, outdata, frames, time, status):
        """This callback is called by sounddevice when it needs more audio data to play."""
        with self._lock:
            if status:
                logger.debug(f"Audio output status: {status}")
            data = np.empty(0, dtype=np.int16)

            # get next item from queue if there is still space in the buffer
            while len(data) < frames and len(self._queue) > 0:
                item = self._queue.pop(0)
                frames_needed = frames - len(data)
                data = np.concatenate((data, item[:frames_needed]))
                if len(item) > frames_needed:
                    self._queue.insert(0, item[frames_needed:])

            self._frame_count += len(data)

            # fill the rest of the frames with zeros if there is no more data
            if len(data) < frames:
                data = np.concatenate((data, np.zeros(frames - len(data), dtype=np.int16)))

        outdata[:] = data.reshape(-1, 1)

    def reset_frame_count(self):
        self._frame_count = 0

    def get_frame_count(self):
        return self._frame_count

    async def client_callback(self, content: np.ndarray):
        """This function can be passed to the audio_output_callback field of the RealtimeClientBase."""
        with self._lock:
            self._queue.append(content)

    async def add_audio(self, audio_content: AudioContent) -> None:
        """This function is used to add audio to the queue for playing.

        It first checks if there is a AudioFrame in the inner_content of the AudioContent.
        If not, it checks if the data is a numpy array, bytes, or a string and converts it to a numpy array.
        """
        with self._lock:
            if audio_content.inner_content and isinstance(audio_content.inner_content, AudioFrame):
                self._queue.append(audio_content.inner_content.to_ndarray())
                return
            if isinstance(audio_content.data, np.ndarray):
                self._queue.append(audio_content.data)
                return
            if isinstance(audio_content.data, bytes):
                self._queue.append(np.frombuffer(audio_content.data, dtype=self.dtype))
                return
            if isinstance(audio_content.data, str):
                self._queue.append(np.frombuffer(audio_content.data.encode(), dtype=self.dtype))
                return
            logger.error(f"Unknown audio content: {audio_content}")
