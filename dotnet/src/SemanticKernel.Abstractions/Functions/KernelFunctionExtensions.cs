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
    /// <para>
    /// The provided <see cref="Kernel"/> will be used by default when none is provided using the arguments in <see cref="AIFunction.InvokeAsync"/> or when a null <see cref="Kernel"/> is used when invoking <see cref="KernelFunction.InvokeAsync"/> method.
    /// </para>
    /// <para>
    /// <paramref name="useFullyQualifiedName"/> is useful when you want to use a <see cref="KernelFunction"/> in an environment that only understand the Low-level <see cref="AIFunction"/> abstraction where there is no concept of plugin name.
    /// By enabling this flag, the resulting <see cref="KernelFunction.Name"/> will be prefixed by the plugin name i.e.: "PluginName_FunctionName".
    /// </para>
    /// </remarks>
    /// <param name="kernelFunction">The kernel function to clone.</param>
    /// <param name="kernel">The kernel to use for the cloned function.</param>
    /// <param name="pluginName">Optional plugin name to use for the cloned function.</param>
    /// <param name="useFullyQualifiedName">Optional flag that indicates whenever the resulting cloned function <see cref="KernelFunction.Name"/> should be prefixed by the plugin name i.e.: "PluginName_FunctionName". Defaults to true.</param>
    [Experimental("SKEXP0001")]
    public static KernelFunction Clone(this KernelFunction kernelFunction, Kernel? kernel = null, string? pluginName = null, bool? useFullyQualifiedName = true)
    {
        var clone = kernelFunction.Clone(pluginName ?? kernelFunction.PluginName);
        clone.UseFullyQualifiedName = useFullyQualifiedName ?? true;
        clone.Kernel = kernel;

        return clone;
    }
}
