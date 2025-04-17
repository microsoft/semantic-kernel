// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="ConversationStateExtensionsManager"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class ConversationStateExtensionsManagerExtensions
{
    /// <summary>
    /// Registers plugins required by all conversation state extensions contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="conversationStateExtensionsManager">The conversation state manager to get plugins from.</param>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public static void RegisterPlugins(this ConversationStateExtensionsManager conversationStateExtensionsManager, Kernel kernel)
    {
        kernel.Plugins.AddFromFunctions("Tools", conversationStateExtensionsManager.AIFunctions.Select(x => x.AsKernelFunction()));
    }
}
