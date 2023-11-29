// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for working with <see cref="IKernelPlugin"/>s and collections of them.</summary>
internal static class IKernelPluginExtensions
{
    /// <summary>Gets a collection of <see cref="KernelPluginFunctionMetadata"/> instances, one for every function in every plugin in the plugins collection.</summary>
    /// <param name="plugins">The plugins collection.</param>
    /// <returns>A list of metadata over every function in the plugins collection</returns>
    public static IList<KernelPluginFunctionMetadata> GetFunctionsMetadata(this IEnumerable<IKernelPlugin> plugins)
    {
        Verify.NotNull(plugins);

        List<KernelPluginFunctionMetadata> metadata = new();
        foreach (IKernelPlugin plugin in plugins)
        {
            foreach (KernelFunction function in plugin)
            {
                metadata.Add(new KernelPluginFunctionMetadata(function.Metadata) { PluginName = plugin.Name });
            }
        }

        return metadata;
    }
}
