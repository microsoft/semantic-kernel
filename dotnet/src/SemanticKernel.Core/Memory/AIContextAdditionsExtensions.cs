// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="ICollection{KernelPlugin}"/> to add <see cref="AIContextPart"/> plugins.
/// </summary>
[Experimental("SKEXP0130")]
public static class AIContextAdditionsExtensions
{
    /// <summary>
    /// Registers the <see cref="AIFunction"/> objects available on the provided <see cref="AIContextPart"/> as a plugin.
    /// </summary>
    /// <param name="plugins">The plugins collection to register the <see cref="AIFunction"/> objects on.</param>
    /// <param name="aiContextAdditions">The <see cref="AIContextPart"/> to get plugins from.</param>
    /// <param name="pluginName">The name to give to the plugin.</param>
    public static void AddFromAIContextPart(this ICollection<KernelPlugin> plugins, AIContextPart aiContextAdditions, string pluginName)
    {
        plugins.AddFromFunctions(pluginName, aiContextAdditions.AIFunctions.Select(x => x.AsKernelFunction()));
    }
}
