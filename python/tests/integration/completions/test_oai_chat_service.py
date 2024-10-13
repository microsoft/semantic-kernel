# Copyright (c) Microsoft. All rights reserved.
import os

import pytest
from openai import AsyncOpenAI

import semantic_kernel.connectors.ai.open_ai as sk_oai
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import (
    OpenAISettings,
)
from semantic_kernel.contents.chat_history import ChatHistory


@pytest.mark.asyncio
async def test_oai_chat_service_with_yaml_jinja2(setup_tldr_function_for_oai_models):
    kernel, _, _ = setup_tldr_function_for_oai_models
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_service(
        sk_oai.OpenAIChatCompletion(
            service_id="chat-gpt",
            ai_model_id="gpt-3.5-turbo",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
    )

    plugins_directory = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins"
    )

    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="TestFunctionYamlJinja2"
    )
    assert plugin is not None
    assert plugin["TestFunctionJinja2"] is not None

    chat_history = ChatHistory()
    chat_history.add_system_message("Assistant is a large language model")
    chat_history.add_user_message("I love parrots.")

    result = await kernel.invoke(
        plugin["TestFunctionJinja2"], chat_history=chat_history
    )
    assert result is not None
    assert len(str(result.value)) > 0


@pytest.mark.asyncio
async def test_oai_chat_service_with_yaml_handlebars(
    setup_tldr_function_for_oai_models,
):
    kernel, _, _ = setup_tldr_function_for_oai_models

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head

@pytest.mark.asyncio
async def test_oai_chat_service_with_plugins(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models
>>>>>>> ms/small_fixes

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

@pytest.mark.asyncio
async def test_oai_chat_service_with_plugins(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models
>>>>>>> ms/small_fixes

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_service(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        sk_oai.OpenAIChatCompletion(
            service_id="chat-gpt",
            ai_model_id="gpt-3.5-turbo",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
    )

    plugins_directory = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins"
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
    )

    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="TestFunctionYamlHandlebars"
    )
    assert plugin is not None
    assert plugin["TestFunctionHandlebars"] is not None
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
    )

    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="TestFunctionYamlJinja2"
    )
    assert plugin is not None
    assert plugin["TestFunctionJinja2"] is not None
=======
        sk_oai.OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id),
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat-gpt", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

<<<<<<< div
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
=======
>>>>>>> Stashed changes
    )

    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="TestFunctionYamlJinja2"
    )
    assert plugin is not None
    assert plugin["TestFunctionJinja2"] is not None
=======
        sk_oai.OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id),
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat-gpt", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

    chat_history = ChatHistory()
    chat_history.add_system_message("Assistant is a large language model")
    chat_history.add_user_message("I love parrots.")

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    result = await kernel.invoke(
        plugin["TestFunctionHandlebars"], chat_history=chat_history
    )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    result = await kernel.invoke(
        plugin["TestFunctionHandlebars"], chat_history=chat_history
    )
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    result = await kernel.invoke(
        plugin["TestFunctionJinja2"], chat_history=chat_history
    )
    assert result is not None
    assert len(str(result.value)) > 0
=======
@pytest.mark.asyncio
async def test_oai_chat_service_with_plugins_with_provided_client(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models
>>>>>>> ms/small_fixes


@pytest.mark.asyncio
async def test_oai_chat_service_with_yaml_handlebars(
    setup_tldr_function_for_oai_models,
):
    kernel, _, _ = setup_tldr_function_for_oai_models

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_service(
        sk_oai.OpenAIChatCompletion(
            service_id="chat-gpt",
            ai_model_id="gpt-3.5-turbo",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
<<<<<<< main
    )

    plugins_directory = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins"
    )

    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="TestFunctionYamlHandlebars"
    )
    assert plugin is not None
    assert plugin["TestFunctionHandlebars"] is not None

    chat_history = ChatHistory()
    chat_history.add_system_message("Assistant is a large language model")
    chat_history.add_user_message("I love parrots.")
=======
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat-gpt", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_chat_stream_service_with_plugins(setup_tldr_function_for_oai_models, get_aoai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="chat_completion", deployment_name=deployment_name, endpoint=endpoint, api_key=api_key
        ),
        overwrite=True,
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat_completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)

    arguments = KernelArguments(input=text_to_summarize)

    result = None
    async for message in kernel.invoke_stream(tldr_function, arguments):
        result = message[0] if not result else result + message[0]
    output = str(result)
>>>>>>> ms/small_fixes

    result = await kernel.invoke(
        plugin["TestFunctionHandlebars"], chat_history=chat_history
    )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    assert result is not None
    assert len(str(result.value)) > 0
