// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Common configuration for planner instances.
/// </summary>
public sealed class SequentialPlannerConfig : PlannerConfigBase
{
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
}
