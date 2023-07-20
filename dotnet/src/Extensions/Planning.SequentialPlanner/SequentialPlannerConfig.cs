// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Common configuration for planner instances.
/// </summary>
public sealed class SequentialPlannerConfig
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
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Whether to allow missing functions in the plan on creation.
    /// If set to true, the plan will be created with missing functions as no-op steps.
    /// If set to false (default), the plan creation will fail if any functions are missing.
    /// </summary>
    public bool AllowMissingFunctions { get; set; } = false;

    /// <summary>
    /// Optional callback to get the available functions for planning.
    /// </summary>
    public Func<SequentialPlannerConfig, string?, CancellationToken, Task<IOrderedEnumerable<FunctionView>>>? GetAvailableFunctionsAsync { get; set; }

    /// <summary>
    /// Optional callback to get a function by name.
    /// </summary>
    public Func<string, string, ISKFunction?>? GetSkillFunction { get; set; }
}
