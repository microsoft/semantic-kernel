# Copyright (c) Microsoft. All rights reserved.

from typing import List

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction


async def aggregate_chunked_results_async(
    func: SKFunction, chunked_results: List[str], context: SKContext
) -> SKContext:
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
