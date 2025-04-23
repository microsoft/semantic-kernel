// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="ConversationStatePartsManager"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class ConversationStatePartsManagerExtensions
{
    /// <summary>
    /// Registers plugins required by all conversation state parts contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="conversationStatePartsManager">The conversation state manager to get plugins from.</param>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public static void RegisterPlugins(this ConversationStatePartsManager conversationStatePartsManager, Kernel kernel)
    {
        kernel.Plugins.AddFromFunctions("Tools", conversationStatePartsManager.AIFunctions.Select(x => x.AsKernelFunction()));
    }
}
