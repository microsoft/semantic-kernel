// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="AIFunction"/>.
/// </summary>
public static class AIFunctionExtensions
{
    /// <summary>
    /// Converts an <see cref="AIFunction"/> to a <see cref="KernelFunction"/> if it is not already one.
    /// </summary>
    /// <param name="aiFunction">The AI function to convert.</param>
    /// <returns>The converted <see cref="KernelFunction"/>.</returns>
    [Experimental("SKEXP0001")]
    public static KernelFunction AsKernelFunction(this AIFunction aiFunction)
    {
        Verify.NotNull(aiFunction);
        return aiFunction is KernelFunction kf
            ? kf
            : new AIFunctionKernelFunction(aiFunction);
    }

    /// <summary>
    /// Invokes the <see cref="AIFunction"/> providing a <see cref="Kernel"/> and returns its result.
    /// </summary>
    /// <param name="aiFunction">Represents the AI function to be executed.</param>
    /// <param name="kernel"><see cref="Kernel"/> instance to be used when the <see cref="AIFunction"/> is a <see cref="KernelFunction"/>.</param>
    /// <param name="functionArguments">Contains the arguments required for the AI function execution.</param>
    /// <param name="cancellationToken">Allows for the operation to be canceled if needed.</param>
    /// <returns>The result of the function execution.</returns>
    [Experimental("SKEXP0001")]
    public static ValueTask<object?> InvokeAsync(this AIFunction aiFunction, Kernel kernel, AIFunctionArguments? functionArguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(aiFunction);

        AIFunctionArguments? functionArgumentsClone = null;
        if (aiFunction is KernelFunction)
        {
            // If the AIFunction is a KernelFunction inject the provided kernel in the cloned arguments
            functionArgumentsClone = new AIFunctionArguments(functionArguments)
                .AddKernel(kernel);
        }

        return aiFunction.InvokeAsync(functionArgumentsClone ?? functionArguments, cancellationToken);
    }
}
