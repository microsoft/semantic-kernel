import pytest

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.text import aggregate_chunked_results


@pytest.mark.asyncio
async def test_aggregate_results():
    kernel = Kernel()
    kernel.add_service(sk_oai.OpenAITextCompletion("text-davinci-002", "none", "none", service_id="text-davinci-002"))
    prompt = """
        {{$input}}
        How is that ?
    """

    req_settings = PromptExecutionSettings(
        service_id="text-davinci-002", extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
        ],
        execution_settings={req_settings.service_id: req_settings},
    )

    func = kernel.create_function_from_prompt(
        prompt_template_config=prompt_template_config,
    )

    func.function = lambda function, kernel, arguments, service, execution_settings: FunctionResult(
        function=function, value=arguments["input"], metadata={}
    )

    chunked = [
        "This is a test of the emergency broadcast system.",
        "This is only a test",
        "We repeat, this is only a test? A unit test",
        "A small note! And another? And once again!",
        "Seriously, this is the end.",
        "We're finished. All set. Bye. Done",
    ]
    result = await aggregate_chunked_results(func, chunked, kernel, KernelArguments())
    print(result)
    assert result == "\n".join(chunked)
