# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel.connectors.ai.hugging_face as sk_hf
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_name", "task", "input_str"),
    [
        (
            "patrickvonplaten/t5-tiny-random",
            "text2text-generation",
            "translate English to Dutch: Hello, how are you?",
        ),
        (
            "jotamunz/billsum_tiny_summarization",
            "summarization",
            """
        Summarize: Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males.
    """,
        ),
        ("HuggingFaceM4/tiny-random-LlamaForCausalLM", "text-generation", "Hello, I like sleeping and "),
    ],
    ids=["text2text-generation", "summarization", "text-generation"],
)
async def test_text_completion(model_name, task, input_str):
    kernel = Kernel()

    # Configure LLM service
    kernel.add_text_completion_service(
        service_id=model_name,
        service=sk_hf.HuggingFaceTextCompletion(ai_model_id=model_name, task=task),
    )

    # Define semantic function using SK prompt template language
    sk_prompt = "{{$input}}"

    # Create the semantic function
    function = kernel.create_semantic_function(sk_prompt, max_tokens=25, temperature=0.7, top_p=0.5)

    summary = await kernel.run(function, input_str=input_str)

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_name", "task", "input_str"),
    [
        (
            "patrickvonplaten/t5-tiny-random",
            "text2text-generation",
            "translate English to Dutch: Hello, how are you?",
        ),
        (
            "jotamunz/billsum_tiny_summarization",
            "summarization",
            """
        Summarize: Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males.
    """,
        ),
        # skipped for now, as it takes too long
        ("HuggingFaceM4/tiny-random-LlamaForCausalLM", "text-generation", "Hello, I like sleeping and "),
    ],
    ids=["text2text-generation", "summarization", "text-generation"],
)
async def test_text_completion_stream(model_name, task, input_str):
    kernel = Kernel()

    # Configure LLM service
    kernel.add_text_completion_service(
        service_id=model_name,
        service=sk_hf.HuggingFaceTextCompletion(ai_model_id=model_name, task=task),
    )

    # Define semantic function using SK prompt template language
    sk_prompt = "{{$input}}"

    # Create the semantic function
    function = kernel.create_semantic_function(sk_prompt, max_tokens=25, temperature=0.7, top_p=0.5)

    summary = ""
    async for text in kernel.run_stream(function, input_str=input_str):
        summary += str(text[0])

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0
