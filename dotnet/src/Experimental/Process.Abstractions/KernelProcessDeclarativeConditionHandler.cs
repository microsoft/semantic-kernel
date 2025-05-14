// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a declarative event handler for a process.
/// </summary>
public class KernelProcessDeclarativeConditionHandler
{
    /// <summary>
    /// An optional handler that will always be executed.
    /// </summary>
    public DeclarativeProcessCondition? AlwaysCondition { get; init; }

    /// <summary>
    /// An optional handler that will be executed if no other condition is met.
    /// </summary>
    public DeclarativeProcessCondition? DefaultCondition { get; init; }

    /// <summary>
    /// The list of eval-based handlers.
    /// </summary>
    public List<DeclarativeProcessCondition>? EvalConditions { get; init; } = [];
}
