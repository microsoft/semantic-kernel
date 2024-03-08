# Copyright (c) Microsoft. All rights reserved.

import sys

import pytest

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if sys.version_info >= (3, 9):
    import semantic_kernel.connectors.ai.google_palm as sk_gp


@pytest.fixture(scope="function")
def setup_tldr_function_for_oai_models(kernel: Kernel):
    # Define semantic function using SK prompt template language
    prompt = """
    {{$input}}

    (hyphenated words count as 1 word)
    Give me the TLDR in exactly 5 words:
    """

    # User input
    text_to_summarize = """
        1) A robot may not injure a human being or, through inaction,
        allow a human being to come to harm.

        2) A robot must obey orders given it by human beings except where
        such orders would conflict with the First Law.

        3) A robot must protect its own existence as long as such protection
        does not conflict with the First or Second Law.
    """

    print("TLDR: ")
    print(text_to_summarize)
    print()
    yield kernel, prompt, text_to_summarize


@pytest.fixture(scope="function")
def setup_summarize_conversation_using_plugin(kernel: Kernel):
    ChatTranscript = """John: Hello, how are you?
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

    yield kernel, ChatTranscript


@pytest.fixture(scope="function")
def setup_gp_text_completion_function(kernel: Kernel, get_gp_config):
    api_key = get_gp_config
    # Configure LLM service
    palm_text_completion = sk_gp.GooglePalmTextCompletion(ai_model_id="models/text-bison-001", api_key=api_key)
    kernel.add_service(palm_text_completion)

    # Define semantic function using SK prompt template language
    prompt = "Hello, I like {{$input}}{{$input2}}"

    exec_settings = PromptExecutionSettings(
        service_id="models/text-bison-001", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(template=prompt, execution_settings=exec_settings)

    # Create the semantic function
    text2text_function = kernel.create_function_from_prompt(
        function_name="hello", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    # User input
    simple_input = "sleeping and "

    yield kernel, text2text_function, simple_input
