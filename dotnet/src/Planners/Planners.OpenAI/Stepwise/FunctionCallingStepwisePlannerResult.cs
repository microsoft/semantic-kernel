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
    public string FinalAnswer { get; internal set; } = string.Empty;

    /// <summary>
    /// Chat history containing the planning process.
    /// </summary>
    public ChatHistory? ChatHistory { get; internal set; }

    /// <summary>
    /// Number of iterations performed by the planner.
    /// </summary>
    public int Iterations { get; internal set; } = 0;
}
