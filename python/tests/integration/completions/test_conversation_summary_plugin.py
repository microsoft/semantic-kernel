# Copyright (c) Microsoft. All rights reserved.


import pytest
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
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
<<<<<<< Updated upstream
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
=======
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
=======
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.core_plugins.conversation_summary_plugin import (
    ConversationSummaryPlugin,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_azure_summarize_conversation_using_plugin(
    setup_summarize_conversation_using_plugin,
):
    kernel, chatTranscript = setup_summarize_conversation_using_plugin

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    service_id = "text_completion"

    execution_settings = PromptExecutionSettings(
        service_id=service_id,
        max_tokens=ConversationSummaryPlugin._max_tokens,
        temperature=0.1,
        top_p=0.5,
    )
    prompt_template_config = PromptTemplateConfig(
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(sk_oai.AzureTextCompletion(service_id=service_id))

    conversationSummaryPlugin = kernel.add_plugin(
        ConversationSummaryPlugin(prompt_template_config), "conversationSummary"
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(
        lambda: kernel.invoke(
            conversationSummaryPlugin["SummarizeConversation"], arguments
        )
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    )

=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
        api_key = os.environ["AzureOpenAI__ApiKey"]
        endpoint = os.environ["AzureOpenAI__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = get_aoai_config
        deployment_name = "gpt-35-turbo-instruct"

    service_id = "text_completion"

    execution_settings = PromptExecutionSettings(
        service_id=service_id, max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of" " the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(
        sk_oai.AzureTextCompletion(
            service_id=service_id, deployment_name=deployment_name, endpoint=endpoint, api_key=api_key
        ),
    )

    conversationSummaryPlugin = kernel.import_plugin(
        ConversationSummaryPlugin(kernel, prompt_template_config), "conversationSummary"
>>>>>>> ms/small_fixes
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(lambda: kernel.invoke(conversationSummaryPlugin["SummarizeConversation"], arguments))

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)


@pytest.mark.asyncio
async def test_oai_summarize_conversation_using_plugin(
    setup_summarize_conversation_using_plugin,
):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    kernel, chatTranscript = setup_summarize_conversation_using_plugin

    execution_settings = PromptExecutionSettings(
        service_id="conversation_summary",
        max_tokens=ConversationSummaryPlugin._max_tokens,
        temperature=0.1,
        top_p=0.5,
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(sk_oai.OpenAITextCompletion(service_id="conversation_summary"))

    conversationSummaryPlugin = kernel.add_plugin(
        ConversationSummaryPlugin(prompt_template_config), "conversationSummary"
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(
        lambda: kernel.invoke(
            conversationSummaryPlugin["SummarizeConversation"], arguments
        )
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
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
    )

=======
=======
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    )

=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    _, chatTranscript = setup_summarize_conversation_using_plugin

    # Even though the kernel is scoped to the function, it appears that
    # it is shared because adding the same plugin throws an error.
    # Create a new kernel for this test.
    kernel = sk.Kernel()

    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.openai_settings_from_dot_env()

    execution_settings = PromptExecutionSettings(
        service_id="conversation_summary", max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of" " the conversation.",
        execution_settings=execution_settings,
    )

    kernel.add_service(
        sk_oai.OpenAITextCompletion(
            service_id="conversation_summary", ai_model_id="gpt-3.5-turbo-instruct", api_key=api_key, org_id=org_id
        ),
    )

    conversationSummaryPlugin = kernel.import_plugin(
        ConversationSummaryPlugin(kernel, prompt_template_config), "conversationSummary"
>>>>>>> ms/small_fixes
    )

    arguments = KernelArguments(input=chatTranscript)

    summary = await retry(lambda: kernel.invoke(conversationSummaryPlugin["SummarizeConversation"], arguments))

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(chatTranscript)
