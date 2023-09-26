// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Interface for planner that creates a Stepwise plan using Mrkl systems.
/// </summary>
public interface IStepwisePlanner
{
    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="SKException">Thrown when the plan cannot be created.</exception>
    Plan CreatePlan(string goal);
}
