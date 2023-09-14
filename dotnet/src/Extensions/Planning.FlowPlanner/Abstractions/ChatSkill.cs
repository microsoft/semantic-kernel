// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Chat skill which encapsulates the interface to get latest chat input and history from context maintained by orchestrator.
/// It is recommended to use this class as base class for chat skills and functions.
/// </summary>
/// <remarks>
/// # Create skills
/// There are two ways to instantiate a chat skill:
/// 1. Reflection by planner. To support that the skill should either have a parameter-less constructor or a constructor with single <see cref="SKContext"/> parameter.
/// 2. Register in global skill collection and pass to the Planner.
/// </remarks>
public abstract class ChatSkill
{
    /// <summary>
    /// Get <see cref="ChatHistory"/> from context.
    /// </summary>
    /// <param name="context">context</param>
    /// <returns>The chat history</returns>
    protected ChatHistory? GetChatHistory(SKContext context)
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
    protected string GetChatInput(SKContext context)
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
    protected void PromptInput(SKContext context)
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
    protected void ExitLoop(SKContext context, string? response = null)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!context.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
        {
            context.Variables.Set(Constants.ChatSkillVariables.ExitLoopName, response ?? string.Empty);
        }
    }
}
