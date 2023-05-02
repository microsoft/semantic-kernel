// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using Microsoft.SemanticKernel.Planning.Sequential;

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for the planner.
/// </summary>
public class PlannerOptions
{
    public const string PropertyName = "Planner";

    /// <summary>
    /// Whether to enable the planner.
    /// </summary>
    public bool Enabled { get; set; } = false;

    /// <summary>
    /// The directory containing semantic skills to include in the planner's list of available functions.
    /// </summary>
    public string? SemanticSkillsDirectory { get; set; }

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
    public HashSet<string> ExcludedSkills { get; set; } = new();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; set; } = new();

    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    public HashSet<string> IncludedFunctions { get; set; } = new();

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    [Range(1, int.MaxValue)]
    public int MaxTokens { get; set; } = 1024;

    /// <summary>
    /// Convert to a <see cref="SequentialPlannerConfig"/> instance.
    /// </summary>
    public SequentialPlannerConfig ToSequentialPlannerConfig()
    {
        SequentialPlannerConfig config = new()
        {
            RelevancyThreshold = this.RelevancyThreshold,
            MaxRelevantFunctions = this.MaxRelevantFunctions,
            MaxTokens = this.MaxTokens,
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
