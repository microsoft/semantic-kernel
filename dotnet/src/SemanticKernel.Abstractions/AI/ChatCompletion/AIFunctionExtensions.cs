// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="AIFunction"/>.
/// </summary>
public static class AIFunctionExtensions
{
    /// <summary>
    /// Converts an <see cref="AIFunction"/> to a <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="aiFunction">The AI function to convert.</param>
    /// <returns>The converted <see cref="KernelFunction"/>.</returns>
    [Experimental("SKEXP0001")]
    public static KernelFunction AsKernelFunction(this AIFunction aiFunction)
    {
        Verify.NotNull(aiFunction);
        return new AIFunctionKernelFunction(aiFunction);
    }
}
