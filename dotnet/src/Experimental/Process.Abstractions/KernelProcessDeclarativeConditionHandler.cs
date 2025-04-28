// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a declarative event handler for a process.
/// </summary>
public class KernelProcessDeclarativeConditionHandler
{
    /// <summary>
    /// The optional default handler.
    /// </summary>
    public DeclarativeProcessCondition? Default { get; init; }

    /// <summary>
    /// The list of state-based handlers.
    /// </summary>
    public List<DeclarativeProcessCondition>? StateConditions { get; init; } = [];

    /// <summary>
    /// The list of semantic-based handlers.
    /// </summary>
    public List<DeclarativeProcessCondition>? SemanticConditions { get; init; } = [];
}
