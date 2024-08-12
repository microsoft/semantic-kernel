// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents function choice behavior configuration produced by a <see cref="FunctionChoiceBehavior" />.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class FunctionChoiceBehaviorConfiguration
{
    /// <summary>
    /// Represents an AI model's decision-making strategy for calling functions.
    /// </summary>
    public FunctionChoice Choice { get; internal init; }

    /// <summary>
    /// The functions available for AI model.
    /// </summary>
    public IReadOnlyList<KernelFunction>? Functions { get; internal init; }

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by the AI connector.
    /// </summary>
    public bool AutoInvoke { get; internal init; } = true;

    /// <summary>
    /// Specifies whether validation against a specified list of functions is required before allowing AI connector to invoke it.
    /// </summary>
    public bool AllowAnyRequestedKernelFunction { get; internal set; }
}
