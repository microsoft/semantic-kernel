// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="KernelFunction"/>.</summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Creates a cloned <see cref="KernelFunction"/> for a specific <see cref="Kernel"/>.
    /// This is works best when using it as a <see cref="AIFunction"/> abstraction and you want to enforce the <see cref="Kernel"/> instance
    /// at initialization of the <see cref="AIFunction"/>.
    /// </summary>
    /// <remarks>
    ///
    /// </remarks>
    [Experimental("SKEXP0001")]
    public static KernelFunction Clone(this KernelFunction kernelFunction, Kernel kernel)
    {
        var clone = kernelFunction.Clone();
        clone.Kernel = kernel;

        return clone;
    }
}
