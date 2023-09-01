// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Action;

using Connectors.AI.OpenAI.AzureSdk.FunctionCalling;


/// <summary>
///  A function call for use with the Action Planner
/// </summary>
public class ActionPlanCall : FunctionCall
{
    /// <summary>
    /// Rationale given by the LLM for choosing the function
    /// </summary>
    public string Rationale { get; set; } = string.Empty;
}
