# Copyright (c) Microsoft. All rights reserved.


import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.core_plugins.conversation_summary_plugin import ConversationSummaryPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from tests.utils import retry

CHAT_TRANSCRIPT = """John: Hello, how are you?
Jane: I'm fine, thanks. How are you?
John: I'm doing well, writing some example code.
Jane: That's great! I'm writing some example code too.
John: What are you writing?
Jane: I'm writing a chatbot.
John: That's cool. I'm writing a chatbot too.
Jane: What language are you writing it in?
John: I'm writing it in C#.
Jane: I'm writing it in Python.
John: That's cool. I need to learn Python.
Jane: I need to learn C#.
John: Can I try out your chatbot?
Jane: Sure, here's the link.
John: Thanks!
Jane: You're welcome.
Jane: Look at this poem my chatbot wrote:
Jane: Roses are red
Jane: Violets are blue
Jane: I'm writing a chatbot
Jane: What about you?
John: That's cool. Let me see if mine will write a poem, too.
John: Here's a poem my chatbot wrote:
John: The singularity of the universe is a mystery.
Jane: You might want to try using a different model.
John: I'm using the GPT-2 model. That makes sense.
John: Here is a new poem after updating the model.
John: The universe is a mystery.
John: The universe is a mystery.
John: The universe is a mystery.
Jane: Sure, what's the problem?
John: Thanks for the help!
Jane: I'm now writing a bot to summarize conversations.
Jane: I have some bad news, we're only half way there.
John: Maybe there is a large piece of text we can use to generate a long conversation.
Jane: That's a good idea. Let me see if I can find one. Maybe Lorem Ipsum?
John: Yeah, that's a good idea."""


async def test_azure_summarize_conversation_using_plugin(kernel):
    service_id = "text_completion"

    execution_settings = PromptExecutionSettings(
        service_id=service_id, max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings={service_id: execution_settings},
    )

    kernel.add_service(sk_oai.OpenAIChatCompletion(service_id=service_id))

    conversationSummaryPlugin = kernel.add_plugin(
        ConversationSummaryPlugin(prompt_template_config), "conversationSummary"
    )

    arguments = KernelArguments(input=CHAT_TRANSCRIPT)

    summary = await retry(
        lambda: kernel.invoke(conversationSummaryPlugin["SummarizeConversation"], arguments), retries=5
    )

    output = str(summary).strip().lower()
    print(output)
    assert "john" in output and "jane" in output
    assert len(output) < len(CHAT_TRANSCRIPT)
