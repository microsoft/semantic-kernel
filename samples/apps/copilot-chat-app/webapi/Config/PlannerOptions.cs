// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Planning.Planners;

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for the planner.
/// </summary>
public class PlannerOptions
{
    public const string PropertyName = "Planner";

    /// <summary>
    /// The minimum relevancy score for a function to be considered
    /// </summary>
    public double? RelevancyThreshold { get; set; }

    /// <summary>
    /// The maximum number of relevant functions to include in the plan.
    /// </summary>
    public int MaxRelevantFunctions { get; set; } = 100;

    /// <summary>
    /// A list of skills to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedSkills { get; } = new() { };

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new() { };

    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    public HashSet<string> IncludedFunctions { get; } = new() { };

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    public int MaxTokens { get; set; } = 1024;

    /// <summary>
    /// Convert to a <see cref="PlannerConfig"/> instance.
    /// </summary>
    public PlannerConfig ToPlannerConfig()
    {
        PlannerConfig config = new()
        {
            RelevancyThreshold = RelevancyThreshold,
            MaxRelevantFunctions = MaxRelevantFunctions,
            MaxTokens = MaxTokens,
        };

        this.ExcludedSkills.Clear();
        foreach (var excludedSkill in this.ExcludedSkills)
        {
            config.ExcludedSkills.Add(excludedSkill);
        }

        this.ExcludedFunctions.Clear();
        foreach (var excludedFunction in this.ExcludedFunctions)
        {
            config.ExcludedFunctions.Add(excludedFunction);
        }

        this.IncludedFunctions.Clear();
        foreach (var includedFunction in this.IncludedFunctions)
        {
            config.IncludedFunctions.Add(includedFunction);
        }

        return config;
    }
}
