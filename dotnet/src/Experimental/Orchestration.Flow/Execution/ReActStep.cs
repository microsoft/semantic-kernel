// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

/// <summary>
/// An ReAct (Reasoning-Action-Observation) step in flow execution.
/// </summary>
/// <remarks>
/// https://arxiv.org/pdf/2210.03629.pdf
/// </remarks>
public class ReActStep
{
    /// <summary>
    /// Gets or sets the step number.
    /// </summary>
    [JsonPropertyName("thought")]
    public string? Thought { get; set; }

    /// <summary>
    /// Gets or sets the action of the step
    /// </summary>
    [JsonPropertyName("action")]
    public string? Action { get; set; }

    /// <summary>
    /// Gets or sets the variables for the action
    /// </summary>
    [JsonPropertyName("action_variables")]
    public Dictionary<string, string>? ActionVariables { get; set; }

    /// <summary>
    /// Gets or sets the output of the action
    /// </summary>
    [JsonPropertyName("observation")]
    public string? Observation { get; set; }

    /// <summary>
    /// Gets or sets the output of the system
    /// </summary>
    [JsonPropertyName("final_answer")]
    public string? FinalAnswer { get; set; }

    /// <summary>
    /// The raw response from the action
    /// </summary>
    [JsonPropertyName("original_response")]
    public string? OriginalResponse { get; set; }
}
