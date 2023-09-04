// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Stepwise;

using Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

/// <summary>
///  A function call for use with the Stepwise Planner
/// </summary>
public class StepFunctionCall : FunctionCallResult
{
    /// <summary>
    /// Rationale given by the LLM for choosing the function
    /// </summary>
    public string? Thought { get; set; }

    /// <summary>
    ///  The result of the last action taken
    /// </summary>
    public string? Observation { get; set; }

    /// <summary>
    ///  The final answer to the question
    /// </summary>
    public string? FinalAnswer { get; set; }

    public string? OriginalResponse { get; set; }
}
