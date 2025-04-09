// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;

/// <summary>
/// Extension methods for <see cref="FunctionResult"/>
/// </summary>
// ReSharper disable once InconsistentNaming
public static class FunctionResultExtensions
{
    /// <summary>
    /// Check if we should prompt user for input based on function result.
    /// </summary>
    /// <param name="result">Function result.</param>
    internal static bool IsPromptInput(this FunctionResult result)
    {
        return result.Metadata!.TryGetValue(Constants.ChatPluginVariables.PromptInputName, out object? promptInput)
               && promptInput is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should force the next iteration loop based on function result.
    /// </summary>
    /// <param name="result">Function result.</param>
    internal static bool IsContinueLoop(this FunctionResult result)
    {
        return result.Metadata!.TryGetValue(Constants.ChatPluginVariables.ContinueLoopName, out object? continueLoop)
               && continueLoop is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if we should exit the loop based on function result.
    /// </summary>
    /// <param name="result">Function result.</param>
    /// <param name="response">The response to exit loop</param>
    internal static bool TryGetExitLoopResponse(this FunctionResult result, out string? response)
    {
        if (result.Metadata!.TryGetValue(Constants.ChatPluginVariables.ExitLoopName, out object? exitLoop)
            && exitLoop is string exitLoopResponse)
        {
            response = exitLoopResponse;
            return true;
        }

        response = null;
        return false;
    }

    /// <summary>
    /// Check if we should terminate flow based on function result.
    /// </summary>
    /// <param name="result">Function result.</param>
    public static bool IsTerminateFlow(this FunctionResult result)
    {
        return result.Metadata!.TryGetValue(Constants.ChatPluginVariables.StopFlowName, out object? stopFlow)
               && stopFlow is Constants.ChatPluginVariables.DefaultValue;
    }

    /// <summary>
    /// Check if all arguments to be provided with the flow is available in the context
    /// </summary>
    /// <param name="result">Function result.</param>
    /// <param name="flow">flow</param>
    /// <returns></returns>
    public static bool IsComplete(this FunctionResult result, Flow flow)
    {
        return flow.Provides.All(result.Metadata!.ContainsKey);
    }

    /// <summary>
    /// Get <see cref="ChatHistory"/> from context.
    /// </summary>
    /// <param name="result">Function result.</param>
    /// <returns>The chat history</returns>
    public static ChatHistory? GetChatHistory(this FunctionResult result)
    {
        if (result.Metadata!.TryGetValue(Constants.ActionVariableNames.ChatHistory, out object? chatHistory)
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
    /// <param name="result">Function result.</param>
    /// <returns>The latest chat input.</returns>
    public static string GetChatInput(this FunctionResult result)
    {
        if (result.Metadata!.TryGetValue(Constants.ActionVariableNames.ChatInput, out object? chatInput)
            && chatInput is string chatInputString)
        {
            return chatInputString;
        }

        return string.Empty;
    }
}
