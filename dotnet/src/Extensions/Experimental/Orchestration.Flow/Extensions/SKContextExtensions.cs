// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.FlowExecutor;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Extension methods for <see cref="SKContext"/>
/// </summary>
// ReSharper disable once InconsistentNaming
public static class SKContextExtensions
{
    /// <summary>
    /// Get <see cref="ChatHistory"/> from context.
    /// </summary>
    /// <param name="context">context</param>
    /// <returns>The chat history</returns>
    public static ChatHistory? GetChatHistory(this SKContext context)
    {
        if (context.Variables.TryGetValue(Constants.ActionVariableNames.ChatHistory, out string? chatHistoryText) && !string.IsNullOrEmpty(chatHistoryText))
        {
            return ChatHistorySerializer.Deserialize(chatHistoryText);
        }

        return null;
    }

    /// <summary>
    /// Get latest chat input from context.
    /// </summary>
    /// <param name="context">context</param>
    /// <returns>The latest chat input.</returns>
    public static string GetChatInput(this SKContext context)
    {
        if (context.Variables.TryGetValue(Constants.ActionVariableNames.ChatInput, out string? chatInput))
        {
            return chatInput;
        }

        return string.Empty;
    }

    /// <summary>
    /// Signal the orchestrator to prompt user for input with current function response.
    /// </summary>
    /// <param name="context">context</param>
    public static void PromptInput(this SKContext context)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!context.Variables.ContainsKey(Constants.ChatSkillVariables.ExitLoopName))
        {
            context.Variables.Set(Constants.ChatSkillVariables.PromptInputName, Constants.ChatSkillVariables.PromptInputValue);
        }
    }

    /// <summary>
    /// Signal the orchestrator to exit out of the AtLeastOnce or ZeroOrMore loop. If response is non-null, that value will be outputted to the user.
    /// </summary>
    /// <param name="context">context</param>
    /// <param name="response">context</param>
    public static void ExitLoop(this SKContext context, string? response = null)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!context.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
        {
            context.Variables.Set(Constants.ChatSkillVariables.ExitLoopName, response ?? string.Empty);
        }
    }

    /// <summary>
    /// Check if should prompt user for input based on current context.
    /// </summary>
    /// <param name="context">context</param>
    internal static bool IsPromptInput(this ContextVariables context)
    {
        return context.TryGetValue(Constants.ChatSkillVariables.PromptInputName, out string? promptInput)
               && promptInput == Constants.ChatSkillVariables.PromptInputValue;
    }
}
