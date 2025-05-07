// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="AIContextBehaviorsManager"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class AIContextBehaviorsManagerExtensions
{
    /// <summary>
    /// Registers plugins required by all <see cref="AIContextBehavior"/> objects contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="aiContextBehaviorsManager">The <see cref="AIContextBehaviorsManager"/> to get plugins from.</param>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public static void RegisterPlugins(this AIContextBehaviorsManager aiContextBehaviorsManager, Kernel kernel)
    {
        kernel.Plugins.AddFromFunctions("Tools", aiContextBehaviorsManager.AIFunctions.Select(x => x.AsKernelFunction()));
    }
}
