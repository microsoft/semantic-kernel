# Copyright (c) Microsoft. All rights reserved.

from pytest import mark


@mark.asyncio
async def test_ai_service_sample():
    from samples.learn_resources.ai_services import main

    await main()


@mark.asyncio
async def test_configuring_prompts(monkeypatch):
    from samples.learn_resources.configuring_prompts import main

    responses = ["Hello, who are you?", "exit"]

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await main()


@mark.asyncio
async def test_creating_functions(monkeypatch):
    from samples.learn_resources.creating_functions import main

    responses = ["What is 3+3?", "exit"]

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await main()


@mark.asyncio
async def test_functions_within_prompts(monkeypatch):
    from samples.learn_resources.functions_within_prompts import main

    responses = ["Hello, who are you?", "exit"]

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await main()


@mark.asyncio
async def test_planner():
    from samples.learn_resources.planner import main

    await main()


@mark.asyncio
async def test_plugin():
    from samples.learn_resources.plugin import main

    await main()


@mark.asyncio
async def test_serializing_prompts(monkeypatch):
    from samples.learn_resources.serializing_prompts import main

    responses = ["Hello, who are you?", "exit"]

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await main()


@mark.asyncio
async def test_templates(monkeypatch):
    from samples.learn_resources.templates import main

    responses = ["Hello, who are you?", "Thanks, see you next time!"]

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await main()


@mark.asyncio
async def test_using_the_kernel():
    from samples.learn_resources.using_the_kernel import main

    await main()


@mark.asyncio
async def test_your_first_prompt(monkeypatch):
    from samples.learn_resources.your_first_prompt import main

    monkeypatch.setattr("builtins.input", lambda _: "I want to send an email to my manager!")
    await main(delay=10)
