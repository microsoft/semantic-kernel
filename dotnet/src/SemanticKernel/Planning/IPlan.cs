// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Interface for a plan executable by the kernel
/// </summary>
public interface IPlan
{
    /// <summary>
    /// State of the plan
    /// </summary>
    ContextVariables State { get; }

    /// <summary>
    /// Root step of the plan
    /// </summary>
    PlanStep Root { get; }

    /// <summary>
    /// Run the next step of the plan
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Variables to use</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The updated plan</returns>
    Task<IPlan> RunNextStepAsync(
        IKernel kernel,
        ContextVariables variables,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// An executable step in a plan
/// </summary>
public class PlanStep
{
    /// <summary>
    /// Description of the step
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Selected skill
    /// </summary>
    [JsonPropertyName("selected_skill")]
    public string SelectedSkill { get; set; } = string.Empty;

    /// <summary>
    /// Selected function
    /// </summary>
    [JsonPropertyName("selected_function")]
    public string SelectedFunction { get; set; } = string.Empty;

    /// <summary>
    /// Named parameters for the function
    /// </summary>
    [JsonPropertyName("named_parameters")]
    public ContextVariables NamedParameters { get; set; } = new();

    /// <summary>
    /// Key used to store the function output of the step in the state
    /// </summary>
    [JsonPropertyName("output_key")]
    public string OutputKey { get; set; } = string.Empty;

    /// <summary>
    /// Key used to store the function output as a plan result in the state
    /// </summary>
    [JsonPropertyName("result_key")]
    public string ResultKey { get; set; } = string.Empty;

    /// <summary>
    /// Sub-steps of the step
    /// </summary>
    [JsonPropertyName("steps")]
    public IList<PlanStep> Steps { get; } = new List<PlanStep>();
}
