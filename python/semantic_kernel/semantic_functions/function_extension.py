# Copyright (c) Microsoft. All rights reserved.

from typing import List

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction


async def aggregate_partionned_results_async(
    func: SKFunction, partitioned_results: List[str], context: SKContext
) -> SKContext:
    """
    Aggregate the results from the partitioned results.
    """
    results = []
    for partition in partitioned_results:
        context.variables.update(partition)
        context = await func.invoke_async(context=context)

        results.append(str(context.variables))

    context.variables.update("\n".join(results))
    return context
