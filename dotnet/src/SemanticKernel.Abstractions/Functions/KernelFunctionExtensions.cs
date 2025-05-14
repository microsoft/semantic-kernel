// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="KernelFunction"/>.</summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Creates a cloned <see cref="KernelFunction"/> for a specific <see cref="Kernel"/>. Useful when this function is used as a lower-level <see cref="AIFunction"/> abstraction directly.
    /// </summary>
    /// <remarks>
    /// The provided <see cref="Kernel"/> will be used by default when none is provided using the arguments in <see cref="AIFunction.InvokeAsync"/> or when a null <see cref="Kernel"/> is used when invoking <see cref="KernelFunction.InvokeAsync"/> method.
    /// </remarks>
    /// <param name="kernelFunction">The <see cref="KernelFunction"/> to clone with a default <see cref="Kernel"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> to use as the default option.</param>
    /// <param name="pluginName">Optional plugin name to use for the new kernel cloned function.</param>
    [Experimental("SKEXP0001")]
    public static KernelFunction WithKernel(this KernelFunction kernelFunction, Kernel? kernel = null, string? pluginName = null)
    {
        var clone = kernelFunction.Clone(pluginName ?? kernelFunction.PluginName);
        clone.Kernel = kernel;

        return clone;
    }
}
