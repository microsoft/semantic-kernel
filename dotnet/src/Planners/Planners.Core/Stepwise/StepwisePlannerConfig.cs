// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.SemanticFunctions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public sealed class StepwisePlannerConfig : PlannerConfigBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="StepwisePlannerConfig"/>
    /// </summary>
    public StepwisePlannerConfig()
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
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    public int MaxIterations { get; set; } = 15;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; } = 0;

    /// <summary>
    /// The configuration to use for the prompt template.
    /// </summary>
    public PromptTemplateConfig? PromptUserConfig { get; set; } = null;

    /// <summary>
    /// A suffix to use within the default prompt template.
    /// </summary>
    public string Suffix { get; set; } = @"Let's break down the problem step by step and think about the best approach. Label steps as they are taken.

Continue the thought process!";
}
