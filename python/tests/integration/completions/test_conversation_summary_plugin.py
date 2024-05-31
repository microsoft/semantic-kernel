# Copyright (c) Microsoft. All rights reserved.


import pytest
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.core_plugins.conversation_summary_plugin import (
    ConversationSummaryPlugin,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_azure_summarize_conversation_using_plugin(setup_summarize_conversation_using_plugin):
    kernel, chatTranscript = setup_summarize_conversation_using_plugin

    service_id = "text_completion"

    execution_settings = PromptExecutionSettings(
        service_id=service_id, max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(sk_oai.AzureTextCompletion(service_id=service_id))

    conversationSummaryPlugin = kernel.add_plugin(
        ConversationSummaryPlugin(kernel, prompt_template_config), "conversationSummary"
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(lambda: kernel.invoke(conversationSummaryPlugin["SummarizeConversation"], arguments))

    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)


@pytest.mark.asyncio
async def test_oai_summarize_conversation_using_plugin(
    setup_summarize_conversation_using_plugin,
):
    kernel, chatTranscript = setup_summarize_conversation_using_plugin

    execution_settings = PromptExecutionSettings(
        service_id="conversation_summary", max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(sk_oai.OpenAITextCompletion(service_id="conversation_summary"))

    conversationSummaryPlugin = kernel.add_plugin(
        ConversationSummaryPlugin(kernel, prompt_template_config), "conversationSummary"
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(lambda: kernel.invoke(conversationSummaryPlugin["SummarizeConversation"], arguments))

    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)
