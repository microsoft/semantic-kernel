// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Result produced by the <see cref="FunctionCallingStepwisePlanner"/>.
/// </summary>
public class FunctionCallingStepwisePlannerResult
{
    /// <summary>
    /// Final result message of the plan.
    /// </summary>
    public string Message { get; } = string.Empty;

    /// <summary>
    /// Chat history containing the planning process.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Create a <see cref="FunctionCallingStepwisePlannerResult"/>
    /// </summary>
    /// <param name="message">The final result message.</param>
    /// <param name="history">The chat history.</param>
    public FunctionCallingStepwisePlannerResult(string message, ChatHistory history)
    {
        this.Message = message;
        this.ChatHistory = history;
    }
}
