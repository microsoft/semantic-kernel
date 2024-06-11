// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents function choice behavior configuration produced by a <see cref="FunctionChoiceBehavior" />.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorConfiguration
{
    /// <summary>
    /// Creates a new instance of the <see cref="FunctionChoiceBehaviorConfiguration"/> class.
    /// </summary>
    internal FunctionChoiceBehaviorConfiguration()
    {
    }

    /// <summary>
    /// Represents an AI model's decision-making strategy for calling functions.
    /// </summary>
    public FunctionChoice Choice { get; internal set; }

    /// <summary>
    /// The functions available for AI model.
    /// </summary>
    public IReadOnlyList<KernelFunction>? Functions { get; internal set; }

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by the AI service/connector.
    /// </summary>
    public bool AutoInvoke { get; internal set; } = true;

    /// <summary>
    /// Specifies whether validation against a specified list of functions is required before allowing the model to request a function from the kernel.
    /// </summary>
    public bool? AllowAnyRequestedKernelFunction { get; internal set; }
}
