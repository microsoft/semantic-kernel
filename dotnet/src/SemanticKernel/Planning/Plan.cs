// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Plan class that is executable by the kernel
/// </summary>
public abstract class Plan : ISKFunction
{
    /// <summary>
    /// State of the plan
    /// </summary>
    [JsonPropertyName("state")]
    public ContextVariables State { get; } = new();

    /// <summary>
    /// Steps of the plan
    /// </summary>
    [JsonPropertyName("steps")]
    public List<Plan> Steps { get; } = new();

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
    /// Run the next step of the plan
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Variables to use</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The updated plan</returns>
    public abstract Task<Plan> RunNextStepAsync(
        IKernel kernel,
        ContextVariables variables,
        CancellationToken cancellationToken = default);

    // ISKFunction implementation

    /// <inheritdoc/>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("skill_name")]
    public string SkillName { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("is_semantic")]
    public bool IsSemantic { get; } = false;

    /// <inheritdoc/>
    [JsonPropertyName("request_settings")]
    public CompleteRequestSettings RequestSettings { get; } = new();

    /// <inheritdoc/>
    public abstract FunctionView Describe();

    /// <inheritdoc/>
    public abstract Task<SKContext> InvokeAsync(string input, SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null, CancellationToken? cancel = null);

    /// <inheritdoc/>
    public abstract Task<SKContext> InvokeAsync(SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null, CancellationToken? cancel = null);

    /// <inheritdoc/>
    public abstract ISKFunction SetAIConfiguration(CompleteRequestSettings settings);

    /// <inheritdoc/>
    public abstract ISKFunction SetAIService(Func<ITextCompletion> serviceFactory);

    /// <inheritdoc/>
    public abstract ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills);
}
