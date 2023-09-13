// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Base class for planner configs
/// </summary>
public abstract class PlannerConfigBase
{
    #region Use these to configure which functions to include/exclude

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

    #endregion Use these to configure which functions to include/exclude
}
