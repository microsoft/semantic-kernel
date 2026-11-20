# Copyright (c) Microsoft. All rights reserved.

import asyncio
import threading

import pytest

from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken


@pytest.mark.parametrize("cancel_before_registration", [False, True])
@pytest.mark.parametrize("cleanup", ["read", "register", "join"])
def test_callback_can_use_cancelled_token(cleanup: str, cancel_before_registration: bool) -> None:
    token = CancellationToken()
    observations: list[bool] = []
    errors: list[BaseException] = []

    def read_token() -> None:
        observations.append(token.is_cancelled())

    def on_cancel() -> None:
        if cleanup == "read":
            read_token()
        elif cleanup == "register":
            token.add_callback(read_token)
            token.cancel()
        else:
            reader = threading.Thread(target=read_token, daemon=True)
            reader.start()
            reader.join(timeout=2)
            assert not reader.is_alive(), "Callback held token lock while waiting for cleanup"

    def cancel_and_register() -> None:
        try:
            if cancel_before_registration:
                token.cancel()
            token.add_callback(on_cancel)
            token.cancel()
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=cancel_and_register, daemon=True)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive(), "Cancellation callback deadlocked while using its token"
    assert not errors
    assert observations == [True]


@pytest.mark.parametrize("cancel_before_link", [False, True])
async def test_link_future_is_cancelled(cancel_before_link: bool) -> None:
    token = CancellationToken()
    future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
    if cancel_before_link:
        token.cancel()
    assert token.link_future(future) is future
    token.cancel()
    assert future.cancelled()


def test_concurrent_cancellation_invokes_callback_once() -> None:
    token = CancellationToken()
    calls: list[bool] = []
    ready = threading.Barrier(6)
    token.add_callback(lambda: calls.append(True))

    def cancel() -> None:
        ready.wait(timeout=5)
        token.cancel()

    workers = [threading.Thread(target=cancel, daemon=True) for _ in range(6)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=5)
    assert all(not worker.is_alive() for worker in workers)
    assert calls == [True]
    assert token.is_cancelled()


def test_callback_exception_propagates_without_repeating_callbacks() -> None:
    token = CancellationToken()
    calls: list[str] = []

    def fail() -> None:
        calls.append("failed")
        raise ValueError("cleanup failed")

    token.add_callback(fail)
    token.add_callback(lambda: calls.append("later"))
    with pytest.raises(ValueError, match="cleanup failed"):
        token.cancel()
    assert token.is_cancelled()
    token.cancel()
    token.add_callback(lambda: calls.append("late registration"))
    assert calls == ["failed", "late registration"]
