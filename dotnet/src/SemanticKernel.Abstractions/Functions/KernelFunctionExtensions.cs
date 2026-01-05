// Copyright (c) Microsoft. All rights reserved.

#if !UNITY
using Microsoft.Extensions.AI;
#endif

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="KernelFunction"/>.</summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Creates a cloned <see cref="KernelFunction"/> for a specific <see cref="Kernel"/>.
    /// </summary>
    /// <remarks>
    /// The provided <see cref="Kernel"/> will be used by default when none is provided using the arguments or when a null <see cref="Kernel"/> is used when invoking <see cref="KernelFunction.InvokeAsync"/> method.
    /// </remarks>
    /// <param name="kernelFunction">The <see cref="KernelFunction"/> to clone with a default <see cref="Kernel"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> to use as the default option.</param>
    /// <param name="pluginName">Optional plugin name to use for the new kernel cloned function.</param>
    public static KernelFunction WithKernel(this KernelFunction kernelFunction, Kernel? kernel = null, string? pluginName = null)
    {
        var clone = kernelFunction.Clone(pluginName ?? kernelFunction.PluginName);
        clone.Kernel = kernel;

        return clone;
    }
}
