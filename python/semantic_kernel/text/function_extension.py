# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel


async def aggregate_chunked_results(
    func: KernelFunction, chunked_results: list[str], kernel: Kernel, arguments: KernelArguments
) -> str:
    """Aggregate the results from the chunked results.

    The caller's arguments are borrowed, not consumed: `input` is set per chunk for the duration of
    the invocation only, and is restored afterwards so callers keep the arguments they passed in.
    """
    results = []
    previous_input = arguments.get("input")
    had_input = "input" in arguments
    try:
        for chunk in chunked_results:
            arguments["input"] = chunk
            result = await func.invoke(kernel, arguments)

            results.append(str(result))
    finally:
        if had_input:
            arguments["input"] = previous_input
        else:
            arguments.pop("input", None)

    return "\n".join(results)
