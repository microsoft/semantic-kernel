// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

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
    /// The configuration to use for the prompt template.
    /// </summary>
    public OpenAIRequestSettings? ModelSettings { get; set; }
}
