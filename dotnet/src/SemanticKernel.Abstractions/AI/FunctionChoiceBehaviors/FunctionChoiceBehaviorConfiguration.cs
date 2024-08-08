// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents function choice behavior configuration produced by a <see cref="FunctionChoiceBehavior" />.
/// </summary>
public sealed class FunctionChoiceBehaviorConfiguration
{
    /// <summary>
    /// Represents an AI model's decision-making strategy for calling functions.
    /// </summary>
    public FunctionChoice Choice { get; internal set; }

    /// <summary>
    /// The functions available for AI model.
    /// </summary>
    public IReadOnlyList<KernelFunction>? Functions { get; internal set; }
}
