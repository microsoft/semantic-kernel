// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Common configuration for planner instances.
/// </summary>
public sealed class SequentialPlannerConfig : PlannerConfigBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialPlannerConfig"/> class.
    /// </summary>
    public SequentialPlannerConfig()
    {
        this.MaxTokens = 1024;
    }

    /// <summary>
    /// Whether to allow missing functions in the plan on creation.
    /// If set to true, the plan will be created with missing functions as no-op steps.
    /// If set to false (default), the plan creation will fail if any functions are missing.
    /// </summary>
    public bool AllowMissingFunctions { get; set; } = false;
}
