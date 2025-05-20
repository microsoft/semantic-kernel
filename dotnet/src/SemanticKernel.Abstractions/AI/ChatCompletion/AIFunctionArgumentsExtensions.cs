// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

internal static class AIFunctionArgumentsExtensions
{
    public const string KernelAIFunctionArgumentKey = $"{nameof(AIFunctionArguments)}_{nameof(Kernel)}";

    internal static AIFunctionArguments AddKernel(this AIFunctionArguments arguments, Kernel kernel)
    {
        Verify.NotNull(arguments);
        arguments[KernelAIFunctionArgumentKey] = kernel;

        return arguments;
    }
}
