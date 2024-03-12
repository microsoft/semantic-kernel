# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from asyncio import AbstractEventLoop, new_event_loop, run_coroutine_threadsafe
from concurrent.futures import Future
from threading import Thread, Lock
from typing import ContextManager, Generic, TypeVar, Optional, Callable

_T = TypeVar("_T")


class _Lazy(Generic[_T]):
    _Factory = Callable[[], _T]

    _lock: Lock
    _factory: _Factory
    _impl: Optional[_T]

    def __init__(self, factory: _Factory):
        self._lock = Lock()
        self._factory = factory
        self._impl = None

    def get(self) -> _T:
        with self._lock:
            if self._impl is None:
                self._impl = self._factory()
            return self._impl


class _ManagedEventLoopImpl(ContextManager):
    _loop: AbstractEventLoop
    _thread: Thread

    def __init__(self, name=None):
        self._loop = new_event_loop()
        self._thread = Thread(
            target=lambda: self._loop.run_forever(), name=name, daemon=True
        )

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()

    def submit(self, coro) -> Future:
        return run_coroutine_threadsafe(coro, self._loop)


# TODO(user): Remove when underlying issue is fixed.
# This is a workaround for https://github.com/grpc/grpc/issues/25364, a grpc
# issue which prevents grpc-asyncio working with multiple event loops in the
# same process. This workaround enables multiple topic publishing as well as
# publish/subscribe from the same process, but does not enable use with other
# grpc-asyncio clients. Once this issue is fixed, roll back the PR which
# introduced this to return to a single event loop per client for isolation.
_global_event_loop: _Lazy[_ManagedEventLoopImpl] = _Lazy(
    lambda: _ManagedEventLoopImpl(name="PubSubLiteEventLoopThread").__enter__()
)


class ManagedEventLoop(ContextManager):
    _loop: _ManagedEventLoopImpl

    def __init__(self, name=None):
        self._loop = _global_event_loop.get()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def submit(self, coro) -> Future:
        return self._loop.submit(coro)
