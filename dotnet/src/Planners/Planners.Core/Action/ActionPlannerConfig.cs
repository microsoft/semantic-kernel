// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Configuration for Action planner instances.
/// </summary>
public sealed class ActionPlannerConfig : PlannerConfigBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ActionPlannerConfig"/> class.
    /// </summary>
    public ActionPlannerConfig()
    {
        this.MaxTokens = 1024;
    }
}
