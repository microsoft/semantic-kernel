// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Extension methods for <see cref="SKContext"/>
/// </summary>
// ReSharper disable once InconsistentNaming
public static class ContextVariablesExtensions
{
    /// <summary>
    /// Check if we should prompt user for input based on current context.
    /// </summary>
    /// <param name="context">context</param>
    internal static bool IsPromptInput(this ContextVariables context)
    {
        return context.TryGetValue(Constants.ChatPluginVariables.PromptInputName, out string? promptInput)
               && promptInput == Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should force the next iteration loop based on current context.
    /// </summary>
    /// <param name="context">context</param>
    internal static bool IsContinueLoop(this ContextVariables context)
    {
        return context.TryGetValue(Constants.ChatPluginVariables.ContinueLoopName, out string? continueLoop)
               && continueLoop == Constants.ChatPluginVariables.DefaultValue;
    }
}
