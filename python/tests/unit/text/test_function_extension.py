import pytest

from semantic_kernel import Kernel
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.text import aggregate_chunked_results


@pytest.mark.asyncio
async def test_aggregate_results():
    kernel = Kernel()

    @kernel_function(name="func")
    def function(kernel, arguments):
        return FunctionResult(
            function=func.metadata,
            value=arguments["input"],
            metadata={},
        )

    func = KernelFunction.from_method(method=function, plugin_name="test")

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
