// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;

/// <summary>
/// Extension methods for <see cref="KernelArguments"/>
/// </summary>
// ReSharper disable once InconsistentNaming
public static class KernelArgumentsExtensions
{
    /// <summary>
    /// Check if we should prompt user for input based on current context.
    /// </summary>
    /// <param name="variables">Context arguments.</param>
    internal static bool IsPromptInput(this KernelArguments variables)
    {
        return variables.TryGetValue(Constants.ChatPluginVariables.PromptInputName, out object? promptInput)
               && promptInput is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should force the next iteration loop based on current context.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    internal static bool IsContinueLoop(this KernelArguments arguments)
    {
        return arguments.TryGetValue(Constants.ChatPluginVariables.ContinueLoopName, out object? continueLoop)
               && continueLoop is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should terminate flow based on current context.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    public static bool IsTerminateFlow(this KernelArguments arguments)
    {
        return arguments.TryGetValue(Constants.ChatPluginVariables.StopFlowName, out object? stopFlow)
               && stopFlow is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if all arguments to be provided with the flow is available in the context
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    /// <param name="flow">flow</param>
    /// <returns></returns>
    public static bool IsComplete(this KernelArguments arguments, Flow flow)
    {
        return flow.Provides.All(arguments.ContainsName);
    }

    /// <summary>
    /// Get <see cref="ChatHistory"/> from context.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    /// <returns>The chat history</returns>
    public static ChatHistory? GetChatHistory(this KernelArguments arguments)
    {
        if (arguments.TryGetValue(Constants.ActionVariableNames.ChatHistory, out object? chatHistory)
            && chatHistory is string chatHistoryText
            && !string.IsNullOrEmpty(chatHistoryText))
        {
            return ChatHistorySerializer.Deserialize(chatHistoryText!);
        }

        return null;
    }

    /// <summary>
    /// Get latest chat input from context.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    /// <returns>The latest chat input.</returns>
    public static string GetChatInput(this KernelArguments arguments)
    {
        if (arguments.TryGetValue(Constants.ActionVariableNames.ChatInput, out object? chatInput)
            && chatInput is string chatInputString)
        {
            return chatInputString;
        }

        return string.Empty;
    }

    /// <summary>
    /// Signal the orchestrator to prompt user for input with current function response.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    public static void PromptInput(this KernelArguments arguments)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!arguments.ContainsName(Constants.ChatPluginVariables.ExitLoopName))
        {
            arguments[Constants.ChatPluginVariables.PromptInputName] = Constants.ChatPluginVariables.DefaultValue;
        }
    }

    /// <summary>
    /// Signal the orchestrator to exit out of the AtLeastOnce or ZeroOrMore loop. If response is non-null, that value will be outputted to the user.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    /// <param name="response">context</param>
    public static void ExitLoop(this KernelArguments arguments, string? response = null)
    {
        // Cant prompt the user for input and exit the execution at the same time
        if (!arguments.ContainsName(Constants.ChatPluginVariables.PromptInputName))
        {
            arguments[Constants.ChatPluginVariables.ExitLoopName] = response ?? string.Empty;
        }
    }

    /// <summary>
    /// Signal the orchestrator to go to the next iteration of the loop in the AtLeastOnce or ZeroOrMore step.
    /// </summary>
    /// <param name="arguments">Context arguments.</param>
    public static void ContinueLoop(this KernelArguments arguments)
    {
        arguments[Constants.ChatPluginVariables.ContinueLoopName] = Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Signal the orchestrator to terminate the flow.
    /// </summary>
    /// <param name="arguments">context</param>
    public static void TerminateFlow(this KernelArguments arguments)
    {
        arguments[Constants.ChatPluginVariables.StopFlowName] = Constants.ChatPluginVariables.DefaultValue;
    }
}
