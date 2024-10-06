# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel


async def aggregate_chunked_results(
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
    func: KernelFunction,
    chunked_results: list[str],
    kernel: Kernel,
    arguments: KernelArguments,
) -> str:
    """Aggregate the results from the chunked results."""
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
=======
    func: KernelFunction, chunked_results: List[str], kernel: Kernel, arguments: KernelArguments
) -> str:
    """
    Aggregate the results from the chunked results.
    """
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
    results = []
    for chunk in chunked_results:
        arguments["input"] = chunk
        result = await func.invoke(kernel, arguments)

        results.append(str(result))

    return "\n".join(results)
