# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel.connectors.ai.hugging_face as sk_hf
import semantic_kernel.connectors.ai.google_palm as sk_gp


@pytest.fixture(
    scope="module",
    params=[
        ("google/flan-t5-base", "text2text-generation"),
        ("facebook/bart-large-cnn", "summarization"),
    ],
)
def setup_hf_text_completion_function(create_kernel, request):
    kernel = create_kernel

    # Configure LLM service
    kernel.add_text_completion_service(
        request.param[0],
        sk_hf.HuggingFaceTextCompletion(request.param[0], task=request.param[1]),
    )

    # Define semantic function using SK prompt template language
    sk_prompt = "Hello, I like {{$input}}{{$input2}}"

    # Create the semantic function
    text2text_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=25, temperature=0.7, top_p=0.5
    )

    # User input
    simple_input = "sleeping and "

    yield kernel, text2text_function, simple_input


@pytest.fixture(scope="module")
def setup_summarize_function(create_kernel):
    # User input (taken from https://en.wikipedia.org/wiki/Whale)
    text_to_summarize = """
        Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males.
    """
    additional_text = """
        The word "whale" comes from the Old English hwæl, from Proto-Germanic *hwalaz,
        from Proto-Indo-European *(s)kwal-o-, meaning "large sea fish".[3][4]
        The Proto-Germanic *hwalaz is also the source of Old Saxon hwal,
        Old Norse hvalr, hvalfiskr, Swedish val, Middle Dutch wal, walvisc, Dutch walvis,
        Old High German wal, and German Wal.[3] Other archaic English forms include wal,
        wale, whal, whalle, whaille, wheal, etc.[5]
    """

    # Define semantic function using SK prompt template language
    sk_prompt = "{{$input}} {{$input2}}"

    kernel = create_kernel

    # Configure LLM service
    kernel.add_text_completion_service(
        "facebook/bart-large-cnn",
        sk_hf.HuggingFaceTextCompletion(
            "facebook/bart-large-cnn", task="summarization"
        ),
    )

    # Create the semantic function
    summarize_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=80, temperature=0, top_p=0.5
    )
    yield kernel, summarize_function, text_to_summarize, additional_text


@pytest.fixture(scope="module")
def setup_tldr_function_for_oai_models(create_kernel):
    kernel = create_kernel

    # Define semantic function using SK prompt template language
    sk_prompt = """
    {{$input}}
    {{$input2}}

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
    yield kernel, sk_prompt, text_to_summarize


@pytest.fixture(scope="module")
def setup_summarize_conversation_using_skill(create_kernel):
    kernel = create_kernel
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


@pytest.fixture(scope="module")
def setup_gp_text_completion_function(create_kernel, get_gp_config):
    kernel = create_kernel
    api_key = get_gp_config
    # Configure LLM service
    palm_text_completion = sk_gp.GooglePalmTextCompletion(
        "models/text-bison-001", api_key
    )
    kernel.add_text_completion_service("models/text-bison-001", palm_text_completion)

    # Define semantic function using SK prompt template language
    sk_prompt = "Hello, I like {{$input}}{{$input2}}"

    # Create the semantic function
    text2text_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=25, temperature=0.7, top_p=0.5
    )

    # User input
    simple_input = "sleeping and "

    yield kernel, text2text_function, simple_input