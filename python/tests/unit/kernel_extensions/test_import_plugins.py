# Copyright (c) Microsoft. All rights reserved.

import os
import random

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.plugin_definition import kernel_function


def test_plugin_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()
    api_key = "test-api-key"
    org_id = "test-org-id"
    kernel.add_text_completion_service(
        "test-completion-service",
        sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id),
    )

    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../..", "test_plugins")
    # path to plugins directory
    plugin = kernel.import_semantic_plugin_from_directory(plugins_directory, "TestPlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("TestFunction") is not None


def test_native_plugin_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()

    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../..", "test_native_plugins")
    # path to plugins directory
    plugin = kernel.import_native_plugin_from_directory(plugins_directory, "TestNativePlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("echoAsync") is not None
    plugin_config = plugin.functions["echoAsync"]
    assert plugin_config.name == "echoAsync"
    assert plugin_config.description == "Echo for input text"


def test_create_semantic_function_succeeds():
    # create a kernel
    kernel = sk.Kernel()

    kernel.add_chat_service(
        "test-completion-service",
        sk_oai.OpenAIChatCompletion("test", "test", ""),
    )

    class GenerateNamesPlugin:
        @kernel_function(description="Generate character names", name="generate_names")
        def generate_names(self) -> str:
            """
            Generate two names.
            Returns:
                str
            """
            names = {"Hoagie", "Hamilton", "Bacon", "Pizza", "Boots", "Shorts", "Tuna"}
            first_name = random.choice(list(names))
            names.remove(first_name)
            second_name = random.choice(list(names))
            return f"{first_name}, {second_name}"

    # import plugins
    _ = kernel.import_plugin(GenerateNamesPlugin(), plugin_name="GenerateNames")

    sk_prompt = """
    Write a short story about two Corgis on an adventure.
    The story must be:
    - G rated
    - Have a positive message
    - No sexism, racism or other bias/bigotry
    - Be exactly {{$paragraph_count}} paragraphs long
    - Be written in this language: {{$language}}
    - The two names of the corgis are {{GenerateNames.generate_names}}
    """

    print(sk_prompt)

    test_func = kernel.create_semantic_function(
        prompt_template=sk_prompt,
        function_name="TestFunction",
        plugin_name="TestPlugin",
        description="Write a short story.",
        max_tokens=500,
        temperature=0.5,
        top_p=0.5,
    )

    assert len(test_func.plugins) > 0
    assert test_func.plugins["GenerateNames"] is not None
