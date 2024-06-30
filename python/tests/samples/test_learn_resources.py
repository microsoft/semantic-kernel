# Copyright (c) Microsoft. All rights reserved.

from pytest import mark

from samples.learn_resources.ai_services import main as ai_services
from samples.learn_resources.configuring_prompts import main as configuring_prompts
from samples.learn_resources.creating_functions import main as creating_functions
from samples.learn_resources.functions_within_prompts import main as functions_within_prompts
from samples.learn_resources.planner import main as planner
from samples.learn_resources.plugin import main as plugin
from samples.learn_resources.serializing_prompts import main as serializing_prompts
from samples.learn_resources.templates import main as templates
from samples.learn_resources.using_the_kernel import main as using_the_kernel
from samples.learn_resources.your_first_prompt import main as your_first_prompt
from tests.samples.test_samples_utils import retry


@mark.asyncio
@mark.parametrize(
    "func,responses",
    [
        (ai_services, []),
        (configuring_prompts, ["Hello, who are you?", "exit"]),
        (creating_functions, ["What is 3+3?", "exit"]),
        (functions_within_prompts, ["Hello, who are you?", "exit"]),
        (planner, []),
        (plugin, []),
        (serializing_prompts, ["Hello, who are you?", "exit"]),
        (templates, ["Hello, who are you?", "Thanks, see you next time!"]),
        (using_the_kernel, []),
        (your_first_prompt, ["I want to send an email to my manager!"]),
    ],
    ids=[
        "ai_services",
        "configuring_prompts",
        "creating_functions",
        "functions_within_prompts",
        "planner",
        "plugin",
        "serializing_prompts",
        "templates",
        "using_the_kernel",
        "your_first_prompt",
    ],
)
async def test_learn_resources(func, responses, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    if func.__module__ == "samples.learn_resources.your_first_prompt":
        await retry(lambda: func(delay=10))
        return
    await retry(lambda: func())
