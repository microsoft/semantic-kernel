// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

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
