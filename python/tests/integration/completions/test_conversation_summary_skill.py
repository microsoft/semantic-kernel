# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from test_utils import retry

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_skills.conversation_summary_skill import (
    ConversationSummarySkill,
)


@pytest.mark.asyncio
async def test_azure_summarize_conversation_using_skill(
    setup_summarize_conversation_using_skill, get_aoai_config
):
    kernel, chatTranscript = setup_summarize_conversation_using_skill

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
        api_key = os.environ["AzureOpenAI__ApiKey"]
        endpoint = os.environ["AzureOpenAI__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = get_aoai_config
        deployment_name = "text-davinci-003"

    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(deployment_name, endpoint, api_key),
    )

    conversationSummarySkill = kernel.import_skill(
        ConversationSummarySkill(kernel), "conversationSummary"
    )

    summary = await retry(
        lambda: kernel.run_async(
            conversationSummarySkill["SummarizeConversation"], input_str=chatTranscript
        )
    )

    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)


@pytest.mark.asyncio
async def test_oai_summarize_conversation_using_skill(
    setup_summarize_conversation_using_skill,
):
    kernel, chatTranscript = setup_summarize_conversation_using_skill

    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.add_text_completion_service(
        "davinci-003",
        sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id=org_id),
    )

    conversationSummarySkill = kernel.import_skill(
        ConversationSummarySkill(kernel), "conversationSummary"
    )

    summary = await retry(
        lambda: kernel.run_async(
            conversationSummarySkill["SummarizeConversation"], input_str=chatTranscript
        )
    )

    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)
