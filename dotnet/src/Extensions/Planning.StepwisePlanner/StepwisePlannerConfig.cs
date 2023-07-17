// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Planning.Stepwise;

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public sealed class StepwisePlannerConfig
{
    /// <summary>
    /// The minimum relevancy score for a function to be considered
    /// </summary>
    /// <remarks>
    /// Depending on the embeddings engine used, the user ask, the step goal
    /// and the functions available, this value may need to be adjusted.
    /// For default, this is set to null to exhibit previous behavior.
    /// </remarks>
    public double? RelevancyThreshold { get; set; }

    /// <summary>
    /// The maximum number of relevant functions to include in the plan.
    /// </summary>
    /// <remarks>
    /// Limits the number of relevant functions as result of semantic
    /// search included in the plan creation request.
    /// <see cref="IncludedFunctions"/> will be included
    /// in the plan regardless of this limit.
    /// </remarks>
    public int MaxRelevantFunctions { get; set; } = 100;

    /// <summary>
    /// A list of skills to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedSkills { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();

    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    public HashSet<string> IncludedFunctions { get; } = new();

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    public int MaxTokens { get; set; } = 1024;

    /// <summary>
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    public int MaxIterations { get; set; } = 100;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; } = 0;
}
