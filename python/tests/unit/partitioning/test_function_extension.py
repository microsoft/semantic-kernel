import pytest

import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai
from semantic_kernel.semantic_functions.function_extension import (
    aggregate_partionned_results_async,
)


@pytest.mark.asyncio
async def test_aggregate_results():
    kernel = sk.create_kernel()

    kernel.config.add_text_backend(
        "davinci-002", sk_oai.OpenAITextCompletion("text-davinci-002", "none", "none")
    )
    sk_prompt = """
        {{$input}}
        How is that ?
    """

    context = kernel.create_new_context()

    func = kernel.create_semantic_function(
        sk_prompt,
        max_tokens=200,
        temperature=0,
        top_p=0.5,
    )

    partitioned = [
        "This is a test of the emergency broadcast system.",
        "This is only a test",
        "We repeat, this is only a test? A unit test",
        "A small note! And another? And once again!",
        "Seriously, this is the end.",
        "We're finished. All set. Bye. Done",
    ]
    context = await aggregate_partionned_results_async(func, partitioned, context)

    assert context.variables.input == "\n".join(partitioned)
