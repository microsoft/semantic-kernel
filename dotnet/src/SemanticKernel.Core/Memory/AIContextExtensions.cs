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
    /// <param name="pluginName">The name to give to the plugin.</param>
    public static void AddFromAIContext(this ICollection<KernelPlugin> plugins, AIContext aiContext, string pluginName)
    {
        if (aiContext.AIFunctions is { Count: > 0 })
        {
            plugins.AddFromFunctions(pluginName, aiContext.AIFunctions.Select(x => x.AsKernelFunction()));
        }
    }
}
