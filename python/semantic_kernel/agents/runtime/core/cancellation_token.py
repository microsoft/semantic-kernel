# Copyright (c) Microsoft. All rights reserved.

import threading
from asyncio import Future
from collections.abc import Callable
from typing import Any

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class CancellationToken:
    """A token used to cancel pending async calls."""

    def __init__(self) -> None:
        """Initialize the CancellationToken."""
        self._cancelled: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._callbacks: list[Callable[[], None]] = []

    def cancel(self) -> None:
        """Cancel pending async calls linked to this cancellation token."""
        with self._lock:
            if self._cancelled:
                return
            self._cancelled = True
            callbacks = self._callbacks.copy()
            self._callbacks.clear()

        # Callbacks may re-enter the token or wait for another thread using it.
        for callback in callbacks:
            callback()

    def is_cancelled(self) -> bool:
        """Check if the CancellationToken has been used."""
        with self._lock:
            return self._cancelled

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Attach a callback that will be called when cancel is invoked."""
        with self._lock:
            if not self._cancelled:
                self._callbacks.append(callback)
                return
        callback()

    def link_future(self, future: Future[Any]) -> Future[Any]:
        """Link a pending async call to a token to allow its cancellation."""

        def _cancel() -> None:
            future.cancel()

        self.add_callback(_cancel)
        return future
