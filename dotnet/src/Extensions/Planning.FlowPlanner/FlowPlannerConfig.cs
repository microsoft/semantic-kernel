// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.Planning.Flow;

/// <summary>
/// Configuration for flow planner instances.
/// </summary>
public sealed class FlowPlannerConfig
{
    /// <summary>
    /// A list of skills to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedSkills { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    public int MaxTokens { get; set; } = 1024;

    /// <summary>
    /// The maximum number of iterations to allow for a step.
    /// </summary>
    public int MaxStepIterations { get; set; } = 10;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; } = 0;

    /// <summary>
    /// Optional. The prompt template override for ReAct engine.
    /// </summary>
    public string? ReActPromptTemplate { get; set; } = null;

    /// <summary>
    /// Optional. The prompt template configuration override for the ReAct engine.
    /// </summary>
    public PromptTemplateConfig? ReActPromptTemplateConfig { get; set; } = null;
}
