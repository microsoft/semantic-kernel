# Copyright (c) Microsoft. All rights reserved.

from typing import List

from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function import KernelFunction


async def aggregate_chunked_results(
    func: KernelFunction, chunked_results: List[str], context: KernelContext
) -> KernelContext:
    """
    Aggregate the results from the chunked results.
    """
    results = []
    for chunk in chunked_results:
        context.variables.update(chunk)
        context = await func.invoke_async(context=context)

        results.append(str(context.variables))

    context.variables.update("\n".join(results))
    return context
