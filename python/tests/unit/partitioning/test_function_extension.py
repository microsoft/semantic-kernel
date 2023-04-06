import semantic_kernel as sk
import pytest
from semantic_kernel.semantic_functions.function_extension import (
    aggregate_partionned_results_async,
)
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)


@pytest.mark.asyncio
async def test_aggregate_results():
    kernel = sk.create_kernel()
    kernel.config.add_openai_completion_backend("test", "test", "test", "test")

    context = kernel.create_new_context()
    config = PromptTemplateConfig.from_completion_parameters()
    template = PromptTemplate("Hello", kernel.prompt_template_engine, config)
    function_config = SemanticFunctionConfig(config, template)

    func = kernel.register_semantic_function("test", "test", function_config)

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
