# Copyright (c) Microsoft. All rights reserved.
import os

import pytest
from mistralai.async_client import MistralAsyncClient

import semantic_kernel.connectors.ai.mistral_ai as sk_mai
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
from semantic_kernel.contents.chat_history import ChatHistory


@pytest.mark.asyncio
async def test_mai_chat_service_with_yaml_jinja2(setup_tldr_function_for_oai_models):
    kernel, _, _ = setup_tldr_function_for_oai_models

    mistralai_settings = MistralAISettings.create()
    api_key = mistralai_settings.api_key.get_secret_value()

    client = MistralAsyncClient(
        api_key=api_key,
    )

    kernel.add_service(
        sk_mai.MistralAIChatCompletion(
            service_id="mistral_ai",
            ai_model_id="open-mistral-7b",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
    )

    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins")

    plugin = kernel.add_plugin(parent_directory=plugins_directory, plugin_name="TestFunctionYamlJinja2")
    assert plugin is not None
    assert plugin["TestFunctionJinja2"] is not None

    chat_history = ChatHistory()
    chat_history.add_system_message("Assistant is a large language model")
    chat_history.add_user_message("I love parrots.")

    result = await kernel.invoke(plugin["TestFunctionJinja2"], chat_history=chat_history)
    assert result is not None
    assert len(str(result.value)) > 0


@pytest.mark.asyncio
async def test_mai_chat_service_with_yaml_handlebars(setup_tldr_function_for_oai_models):
    kernel, _, _ = setup_tldr_function_for_oai_models

    mistralai_settings = MistralAISettings.create()
    api_key = mistralai_settings.api_key.get_secret_value()

    client = MistralAsyncClient(
        api_key=api_key,
    )

    kernel.add_service(
        sk_mai.MistralAIChatCompletion(
            service_id="mistral_ai",
            ai_model_id="open-mistral-7b",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
    )

    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins")

    plugin = kernel.add_plugin(parent_directory=plugins_directory, plugin_name="TestFunctionYamlHandlebars")
    assert plugin is not None
    assert plugin["TestFunctionHandlebars"] is not None

    chat_history = ChatHistory()
    chat_history.add_system_message("Assistant is a large language model")
    chat_history.add_user_message("I love parrots.")

    result = await kernel.invoke(plugin["TestFunctionHandlebars"], chat_history=chat_history)
    assert result is not None
    assert len(str(result.value)) > 0
