// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Planning;

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
