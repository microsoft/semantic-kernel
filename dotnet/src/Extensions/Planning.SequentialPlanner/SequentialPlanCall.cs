// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Sequential;

using Connectors.AI.OpenAI.FunctionCalling;


/// <summary>
/// Function call for use with the Sequential Planner
/// </summary>
public class SequentialPlanCall : FunctionCallResult
{
    /// <summary>
    /// Rationale given by the LLM for choosing the function
    /// </summary>
    public string Rationale { get; set; } = string.Empty;

    /// <summary>
    ///  Enables the model to set a context variable if the function call is a step in a plan
    /// </summary>
    public string? SetContextVariable { get; set; }

    /// <summary>
    ///  Enables the model to append the result of the function call to
    /// another context variable if the function call is a step in a plan
    /// </summary>
    public string? AppendToResult { get; set; }
}
