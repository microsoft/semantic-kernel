# Copyright (c) Microsoft. All rights reserved.

import os
import random

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_plugin_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()
    api_key = "test-api-key"
    org_id = "test-org-id"
    service_id = "text-davinci-003"
    kernel.add_service(
        sk_oai.OpenAITextCompletion(service_id, api_key, org_id, service_id="test-completion-service"),
    )

    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../..", "test_plugins")
    # path to plugins directory
    plugin = kernel.import_plugin_from_prompt_directory(plugins_directory, "TestPlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    func = plugin.functions["TestFunction"]
    assert func is not None


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


def test_create_function_from_prompt_succeeds():
    # create a kernel
    kernel = sk.Kernel()

    kernel.add_service(
        sk_oai.OpenAIChatCompletion("test", "test", "", "test-completion-service"),
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
    kernel.import_plugin(GenerateNamesPlugin(), plugin_name="GenerateNames")

    prompt = """
    Write a short story about two Corgis on an adventure.
    The story must be:
    - G rated
    - Have a positive message
    - No sexism, racism or other bias/bigotry
    - Be exactly {{$paragraph_count}} paragraphs long
    - Be written in this language: {{$language}}
    - The two names of the corgis are {{GenerateNames.generate_names}}
    """

    print(prompt)

    exec_settings = PromptExecutionSettings(extension_data={"max_tokens": 500, "temperature": 0.5, "top_p": 0.5})

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings={"default": exec_settings}
    )

    kernel.create_function_from_prompt(
        prompt_template_config=prompt_template_config,
        function_name="TestFunction",
        plugin_name="TestPlugin",
        description="Write a short story.",
    )
