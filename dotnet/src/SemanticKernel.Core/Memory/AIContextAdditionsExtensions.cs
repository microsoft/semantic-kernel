// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="AIContextPart"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class AIContextAdditionsExtensions
{
    /// <summary>
    /// Registers plugins required by all <see cref="AIContextBehavior"/> objects contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="aiContextAdditions">The <see cref="AIContextPart"/> to get plugins from.</param>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public static void RegisterPlugins(this AIContextPart aiContextAdditions, Kernel kernel)
    {
        kernel.Plugins.AddFromFunctions("Tools", aiContextAdditions.AIFunctions.Select(x => x.AsKernelFunction()));
    }
}
