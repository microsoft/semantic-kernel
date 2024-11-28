// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents function choice behavior configuration produced by a <see cref="FunctionChoiceBehavior" />.
/// </summary>
public sealed class FunctionChoiceBehaviorConfiguration
{
    /// <summary>
    /// Creates a new instance of the <see cref="FunctionChoiceBehaviorConfiguration"/> class.
    /// <param name="options">The behavior options.</param>
    /// </summary>
    internal FunctionChoiceBehaviorConfiguration(FunctionChoiceBehaviorOptions options)
    {
        this.Options = options;
    }

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
    public bool AutoInvoke { get; set; } = true;

    /// <summary>
    /// The behavior options.
    /// </summary>
    public FunctionChoiceBehaviorOptions Options { get; }
}
