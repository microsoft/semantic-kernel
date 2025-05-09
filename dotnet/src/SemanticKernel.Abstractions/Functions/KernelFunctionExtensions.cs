// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="KernelFunction"/>.</summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Creates a cloned <see cref="KernelFunction"/> for a specific <see cref="Kernel"/>.
    /// Use this clone when you want to provide a default <see cref="Kernel"/> instance at it's creation, mostly when using it as a <see cref="AIFunction"/> abstraction.
    /// </summary>
    /// <remarks>
    /// The provided <see cref="Kernel"/> will be used by default when invoking <see cref="AIFunction.InvokeAsync"/> or when a null <see cref="Kernel"/> is used when invoking <see cref="KernelFunction.InvokeAsync"/> method.
    /// </remarks>
    /// <param name="kernelFunction">The kernel function to clone.</param>
    /// <param name="kernel">The kernel to use for the cloned function.</param>
    /// <param name="pluginName">Optional plugin name to use for the cloned function.</param>
    [Experimental("SKEXP0001")]
    public static KernelFunction Clone(this KernelFunction kernelFunction, Kernel? kernel = null, string? pluginName = null)
    {
        var clone = kernelFunction.Clone(pluginName ?? kernelFunction.PluginName);
        clone.UseFullyQualifiedName = true;
        clone.Kernel = kernel;

        return clone;
    }
}
