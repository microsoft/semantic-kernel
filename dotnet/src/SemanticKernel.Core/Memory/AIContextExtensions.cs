// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="ICollection{KernelPlugin}"/> to add <see cref="AIContext"/> plugins.
/// </summary>
[Experimental("SKEXP0130")]
public static class AIContextExtensions
{
    /// <summary>
    /// Registers the <see cref="AIFunction"/> objects available on the provided <see cref="AIContext"/> as a plugin.
    /// </summary>
    /// <param name="plugins">The plugins collection to register the <see cref="AIFunction"/> objects on.</param>
    /// <param name="aiContext">The <see cref="AIContext"/> to get plugins from.</param>
    /// <param name="pluginName">The name to give to the plugin. This will be appended with _x where x is an ascending number, until a unique plugin name is found.</param>
    /// <returns>The chosen plugin name.</returns>
    public static string AddFromAIContext(this ICollection<KernelPlugin> plugins, AIContext aiContext, string pluginName)
    {
        if (aiContext.AIFunctions is { Count: > 0 })
        {
            var originalPluginName = pluginName;
            var counter = 1;

            // Find a unique plugin name by appending a counter if necessary.
            while (plugins.Any(x => x.Name == pluginName))
            {
                pluginName = $"{originalPluginName}_{counter++}";
            }

            plugins.AddFromFunctions(pluginName, aiContext.AIFunctions.Select(x => x.AsKernelFunction()));
        }

        return pluginName;
    }
}
