# Copyright (c) Microsoft. All rights reserved.

import copy
import os

from pytest import mark, param

from samples.learn_resources.ai_services import main as ai_services
from samples.learn_resources.configuring_prompts import main as configuring_prompts
from samples.learn_resources.creating_functions import main as creating_functions
from samples.learn_resources.functions_within_prompts import main as functions_within_prompts
from samples.learn_resources.plugin import main as plugin
from samples.learn_resources.serializing_prompts import main as serializing_prompts
from samples.learn_resources.templates import main as templates
from samples.learn_resources.using_the_kernel import main as using_the_kernel
from samples.learn_resources.your_first_prompt import main as your_first_prompt
from tests.utils import retry

# These environment variable names are used to control which samples are run during integration testing.
# This has to do with the setup of the tests and the services they depend on.
COMPLETIONS_CONCEPT_SAMPLE = "COMPLETIONS_CONCEPT_SAMPLE"

learn_resources = [
    param(
        ai_services,
        [],
        id="ai_services",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        configuring_prompts,
        ["Hello, who are you?", "exit"],
        id="configuring_prompts",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        creating_functions,
        ["What is 3+3?", "exit"],
        id="creating_functions",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        functions_within_prompts,
        ["Hello, who are you?", "exit"],
        id="functions_within_prompts",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        plugin,
        [],
        id="plugin",
        # will run anyway, no services called.
    ),
    param(
        serializing_prompts,
        ["Hello, who are you?", "exit"],
        id="serializing_prompts",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        templates,
        ["Hello, who are you?", "Thanks, see you next time!"],
        id="templates",
        marks=(
            mark.skipif(os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."),
            mark.xfail(reason="This sample is not working as expected."),
        ),
    ),
    param(
        using_the_kernel,
        [],
        id="using_the_kernel",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        your_first_prompt,
        ["I want to send an email to my manager!"],
        id="your_first_prompt",
        marks=mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
]


@mark.parametrize("func,responses", learn_resources)
async def test_learn_resources(func, responses, monkeypatch):
    saved_responses = copy.deepcopy(responses)

    def reset():
        responses.clear()
        responses.extend(saved_responses)

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    if func.__module__ == "samples.learn_resources.your_first_prompt":
        await retry(lambda: func(delay=10), reset=reset)
        return

    await retry(lambda: func(), reset=reset, retries=5)
