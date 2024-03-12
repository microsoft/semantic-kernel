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

import asyncio
import threading
from typing import Generic, TypeVar, Callable, Dict, Awaitable

_Key = TypeVar("_Key")
_Client = TypeVar("_Client")


class ClientMultiplexer(Generic[_Key, _Client]):
    _OpenedClientFactory = Callable[[_Key], _Client]
    _ClientCloser = Callable[[_Client], None]

    _factory: _OpenedClientFactory
    _closer: _ClientCloser
    _lock: threading.Lock
    _live_clients: Dict[_Key, _Client]

    def __init__(
        self,
        factory: _OpenedClientFactory,
        closer: _ClientCloser = lambda client: client.__exit__(None, None, None),
    ):
        self._factory = factory
        self._closer = closer
        self._lock = threading.Lock()
        self._live_clients = {}

    def get_or_create(self, key: _Key) -> _Client:
        with self._lock:
            if key not in self._live_clients:
                self._live_clients[key] = self._factory(key)
            return self._live_clients[key]

    def try_erase(self, key: _Key, client: _Client):
        with self._lock:
            if key not in self._live_clients:
                return
            current_client = self._live_clients[key]
            if current_client is not client:
                return
            del self._live_clients[key]
        self._closer(client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        live_clients: Dict[_Key, _Client]
        with self._lock:
            live_clients = self._live_clients
            self._live_clients = {}
        for topic, client in live_clients.items():
            self._closer(client)


class AsyncClientMultiplexer(Generic[_Key, _Client]):
    _OpenedClientFactory = Callable[[_Key], Awaitable[_Client]]
    _ClientCloser = Callable[[_Client], Awaitable[None]]

    _factory: _OpenedClientFactory
    _closer: _ClientCloser
    _live_clients: Dict[_Key, Awaitable[_Client]]

    def __init__(
        self,
        factory: _OpenedClientFactory,
        closer: _ClientCloser = lambda client: client.__aexit__(None, None, None),
    ):
        self._factory = factory
        self._closer = closer
        self._live_clients = {}

    async def get_or_create(self, key: _Key) -> _Client:
        if key not in self._live_clients:
            self._live_clients[key] = asyncio.ensure_future(self._factory(key))
        future = self._live_clients[key]
        try:
            return await future
        except BaseException as e:
            if key in self._live_clients and self._live_clients[key] is future:
                del self._live_clients[key]
            raise e

    async def try_erase(self, key: _Key, client: _Client):
        if key not in self._live_clients:
            return
        client_future = self._live_clients[key]
        current_client = await client_future
        if current_client is not client:
            return
        # duplicate check after await that no one raced with us
        if (
            key not in self._live_clients
            or self._live_clients[key] is not client_future
        ):
            return
        del self._live_clients[key]
        await self._closer(client)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        live_clients: Dict[_Key, Awaitable[_Client]]
        live_clients = self._live_clients
        self._live_clients = {}
        for topic, client in live_clients.items():
            await self._closer(await client)
