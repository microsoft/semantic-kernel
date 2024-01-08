# Copyright (c) Microsoft. All rights reserved.
import os

import pytest
from openai import AsyncOpenAI
from test_utils import retry

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)


async def clean_up_assistant_resources_async(
    assistant: sk_oai.OpenAIChatCompletion,
) -> None:
    await assistant.delete_thread_async()
    await assistant.delete_assistant_async()


@pytest.mark.asyncio
async def test_oai_chat_service_with_skills(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    kernel.add_chat_service(
        "chat-gpt",
        sk_oai.OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run_async(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_chat_service_with_skills_with_provided_client(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_chat_service(
        "chat-gpt",
        sk_oai.OpenAIChatCompletion(
            ai_model_id="gpt-3.5-turbo",
            async_client=client,
        ),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run_async(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_assistant_initialize(get_oai_config):
    api_key, _ = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    try:
        assistant = sk_oai.OpenAIChatCompletion(
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
            is_assistant=True,
        )

        assert assistant.get_assistant_id() is None

        settings = OpenAIAssistantSettings(
            name="Test Assistant",
            description="Test Assistant",
            instructions="(hyphenated words count as 1 word) Give me the TLDR \
                in as few words as possible. The output must only be one sentence.",
        )

        await assistant.create_assistant_async(settings)

        assert assistant.get_assistant_id() is not None
    finally:
        await clean_up_assistant_resources_async(assistant)


@pytest.mark.asyncio
async def test_oai_assistant(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, _ = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    try:
        assistant = sk_oai.OpenAIChatCompletion(
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
            is_assistant=True,
        )

        settings = OpenAIAssistantSettings(
            name="Test Assistant",
            description="Test Assistant",
            instructions="(hyphenated words count as 1 word) Give me the TLDR \
                in as few words as possible. The output must only be one sentence.",
        )

        await assistant.create_assistant_async(settings)

        kernel.add_chat_service(
            "assistant",
            assistant,
        )

        prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
            max_tokens=2000, temperature=0.7, top_p=0.8
        )

        prompt_template = sk.ChatPromptTemplate(
            sk_prompt, kernel.prompt_template_engine, prompt_config
        )
        prompt_template.add_user_message(text_to_summarize)
        function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
        chat_function = kernel.register_semantic_function(
            "ChatBot", "Chat", function_config
        )

        summary = await retry(lambda: kernel.run_async(chat_function))
        output = str(summary).strip()
        print(f"TLDR using input string: '{output}'")
        assert output is not None
    finally:
        await clean_up_assistant_resources_async(assistant)


@pytest.mark.asyncio
async def test_oai_assistant_with_custom_client(
    setup_tldr_function_for_oai_models, get_oai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    try:
        assistant = sk_oai.OpenAIChatCompletion(
            ai_model_id="gpt-3.5-turbo-1106",
            async_client=client,
            is_assistant=True,
        )

        settings = OpenAIAssistantSettings(
            name="Test Assistant",
            description="Test Assistant",
            instructions="(hyphenated words count as 1 word) Give me the summary \
                in as few words as possible. The output must only be one sentence. Keep it short.",
        )

        await assistant.create_assistant_async(settings)

        kernel.add_chat_service(
            "assistant",
            assistant,
        )

        prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
            max_tokens=2000, temperature=0.7, top_p=0.8
        )

        prompt_template = sk.ChatPromptTemplate(
            sk_prompt, kernel.prompt_template_engine, prompt_config
        )
        prompt_template.add_user_message(text_to_summarize)
        function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
        chat_function = kernel.register_semantic_function(
            "ChatBot", "Chat", function_config
        )

        summary = await retry(lambda: kernel.run_async(chat_function))
        output = str(summary).strip()
        print(f"TLDR using input string: '{output}'")
        assert output is not None
    finally:
        await clean_up_assistant_resources_async(assistant)

async def test_oai_chat_stream_service_with_skills(
    setup_tldr_function_for_oai_models, get_aoai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_chat_service(
        "chat_completion",
        sk_oai.AzureChatCompletion(deployment_name=deployment_name, endpoint=endpoint, api_key=api_key),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    result = []
    async for message in kernel.run_stream_async(tldr_function, input_str=text_to_summarize):
        result.append(message)
    output = "".join(result).strip()

    print(f"TLDR using input string: '{output}'")
    assert len(result) > 1
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100
