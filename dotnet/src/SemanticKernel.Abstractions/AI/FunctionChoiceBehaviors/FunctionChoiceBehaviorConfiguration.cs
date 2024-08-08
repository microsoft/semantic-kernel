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
    /// <param name="options">The options for the behavior.</param>"
    /// </summary>
    internal FunctionChoiceBehaviorConfiguration(FunctionChoiceBehaviorOptions options)
    {
        this.Options = options;
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
    /// The behavior options.
    /// </summary>
    public FunctionChoiceBehaviorOptions Options { get; }

    /// <summary>
    /// Specifies whether validation against a specified list of functions is required before allowing the model to request a function from the kernel.
    /// </summary>
    public bool? AllowAnyRequestedKernelFunction { get; internal set; }
}
