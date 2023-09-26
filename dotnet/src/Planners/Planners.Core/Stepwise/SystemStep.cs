// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// A step in a Stepwise plan.
/// </summary>
public class SystemStep
{
    /// <summary>
    /// Gets or sets the step number.
    /// </summary>
    [JsonPropertyName("thought")]
    public string Thought { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the action of the step
    /// </summary>
    [JsonPropertyName("action")]
    public string Action { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the variables for the action
    /// </summary>
    [JsonPropertyName("action_variables")]
    public Dictionary<string, string> ActionVariables { get; set; } = new();

    /// <summary>
    /// Gets or sets the output of the action
    /// </summary>
    [JsonPropertyName("observation")]
    public string Observation { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the output of the system
    /// </summary>
    [JsonPropertyName("final_answer")]
    public string FinalAnswer { get; set; } = string.Empty;

    /// <summary>
    /// The raw response from the action
    /// </summary>
    [JsonPropertyName("original_response")]
    public string OriginalResponse { get; set; } = string.Empty;
}
