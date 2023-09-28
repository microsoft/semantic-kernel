// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;

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
            context.Variables.Set(Constants.ChatSkillVariables.PromptInputName, Constants.ChatSkillVariables.DefaultValue);
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
    /// Signal the orchestrator to go to the next iteration of the loop in the AtLeastOnce or ZeroOrMore step.
    /// </summary>
    /// <param name="context">context</param>
    public static void ContinueLoop(this SKContext context)
    {
        context.Variables.Set(Constants.ChatSkillVariables.ContinueLoopName, Constants.ChatSkillVariables.DefaultValue);
    }

    /// <summary>
    /// Check if we should prompt user for input based on current context.
    /// </summary>
    /// <param name="context">context</param>
    internal static bool IsPromptInput(this SKContext context)
    {
        return context.Variables.TryGetValue(Constants.ChatSkillVariables.PromptInputName, out string? promptInput)
               && promptInput == Constants.ChatSkillVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should force the next iteration loop based on current context.
    /// </summary>
    /// <param name="context">context</param>
    internal static bool IsContinueLoop(this SKContext context)
    {
        return context.Variables.TryGetValue(Constants.ChatSkillVariables.ContinueLoopName, out string? continueLoop)
               && continueLoop == Constants.ChatSkillVariables.DefaultValue;
    }
}
