// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public sealed class FunctionCallingStepwisePlannerOptions : PlannerOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCallingStepwisePlannerOptions"/>
    /// </summary>
    public FunctionCallingStepwisePlannerOptions() { }

    /// <summary>
    /// The maximum total number of tokens to allow in a completion request,
    /// which includes the tokens from the prompt and completion
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// The ratio of tokens to allocate to the completion request. (prompt / (prompt + completion))
    /// </summary>
    public double MaxTokensRatio { get; set; } = 0.1;

    internal int? MaxCompletionTokens => (this.MaxTokens is null) ? null : (int)(this.MaxTokens * this.MaxTokensRatio);
    internal int? MaxPromptTokens => (this.MaxTokens is null) ? null : (int)(this.MaxTokens * (1 - this.MaxTokensRatio));

    /// <summary>
    /// Delegate to get the prompt template YAML for the initial plan generation phase.
    /// </summary>
    public Func<string>? GetInitialPlanPromptTemplate { get; set; }

    /// <summary>
    /// Delegate to get the prompt template string (system message) for the step execution phase.
    /// </summary>
    public Func<string>? GetStepPromptTemplate { get; set; }

    /// <summary>
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    public int MaxIterations { get; set; } = 15;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; }

    /// <summary>
    /// The prompt execution settings to use for the step execution phase.
    /// </summary>
    public OpenAIPromptExecutionSettings? ExecutionSettings { get; set; }
}
