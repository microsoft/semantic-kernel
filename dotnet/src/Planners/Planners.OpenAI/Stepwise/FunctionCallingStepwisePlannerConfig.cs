// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public sealed class FunctionCallingStepwisePlannerConfig : PlannerConfigBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCallingStepwisePlannerConfig"/>
    /// </summary>
    public FunctionCallingStepwisePlannerConfig()
    {
        this.MaxTokens = 4000;
    }

    /// <summary>
    /// The ratio of tokens to allocate to the completion request. (prompt / (prompt + completion))
    /// </summary>
    public double MaxTokensRatio { get; set; } = 0.1;

    internal int MaxCompletionTokens { get { return (int)(this.MaxTokens * this.MaxTokensRatio); } }

    internal int MaxPromptTokens { get { return (int)(this.MaxTokens * (1 - this.MaxTokensRatio)); } }

    /// <summary>
    /// Delegate to get the prompt template string for the step execution phase.
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
