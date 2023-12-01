// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Extension methods for <see cref="ContextVariables"/>
/// </summary>
// ReSharper disable once InconsistentNaming
public static class ContextVariablesExtensions
{
    /// <summary>
    /// Check if we should prompt user for input based on current context.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    internal static bool IsPromptInput(this ContextVariables variables)
    {
        return variables.TryGetValue(Constants.ChatPluginVariables.PromptInputName, out string? promptInput)
               && promptInput == Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should force the next iteration loop based on current context.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    internal static bool IsContinueLoop(this ContextVariables variables)
    {
        return variables.TryGetValue(Constants.ChatPluginVariables.ContinueLoopName, out string? continueLoop)
               && continueLoop == Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should terminate flow based on current context.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    public static bool IsTerminateFlow(this ContextVariables variables)
    {
        return variables.TryGetValue(Constants.ChatPluginVariables.StopFlowName, out string? stopFlow)
               && stopFlow == Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if all variables to be provided with the flow is available in the context
    /// </summary>
    /// <param name="variables">Context variables.</param>
    /// <param name="flow">flow</param>
    /// <returns></returns>
    public static bool IsComplete(this ContextVariables variables, Flow flow)
    {
        return flow.Provides.All(variables.ContainsKey);
    }

    /// <summary>
    /// Get <see cref="ChatHistory"/> from context.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    /// <returns>The chat history</returns>
    public static ChatHistory? GetChatHistory(this ContextVariables variables)
    {
        if (variables.TryGetValue(Constants.ActionVariableNames.ChatHistory, out string? chatHistoryText) && !string.IsNullOrEmpty(chatHistoryText))
        {
            return ChatHistorySerializer.Deserialize(chatHistoryText);
        }

        return null;
    }

    /// <summary>
    /// Get latest chat input from context.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    /// <returns>The latest chat input.</returns>
    public static string GetChatInput(this ContextVariables variables)
    {
        if (variables.TryGetValue(Constants.ActionVariableNames.ChatInput, out string? chatInput))
        {
            return chatInput;
        }

        return string.Empty;
    }

    /// <summary>
    /// Signal the orchestrator to prompt user for input with current function response.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    public static void PromptInput(this ContextVariables variables)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!variables.ContainsKey(Constants.ChatPluginVariables.ExitLoopName))
        {
            variables.Set(Constants.ChatPluginVariables.PromptInputName, Constants.ChatPluginVariables.DefaultValue);
        }
    }

    /// <summary>
    /// Signal the orchestrator to exit out of the AtLeastOnce or ZeroOrMore loop. If response is non-null, that value will be outputted to the user.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    /// <param name="response">context</param>
    public static void ExitLoop(this ContextVariables variables, string? response = null)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!variables.ContainsKey(Constants.ChatPluginVariables.PromptInputName))
        {
            variables.Set(Constants.ChatPluginVariables.ExitLoopName, response ?? string.Empty);
        }
    }

    /// <summary>
    /// Signal the orchestrator to go to the next iteration of the loop in the AtLeastOnce or ZeroOrMore step.
    /// </summary>
    /// <param name="variables">Context variables.</param>
    public static void ContinueLoop(this ContextVariables variables)
    {
        variables.Set(Constants.ChatPluginVariables.ContinueLoopName, Constants.ChatPluginVariables.DefaultValue);
    }

    /// <summary>
    /// Signal the orchestrator to terminate the flow.
    /// </summary>
    /// <param name="variables">context</param>
    public static void TerminateFlow(this ContextVariables variables)
    {
        variables.Set(Constants.ChatPluginVariables.StopFlowName, Constants.ChatPluginVariables.DefaultValue);
    }
}
