// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// The context to be provided by the choice behavior consumer in order to obtain the choice behavior configuration.
/// </summary>
public class FunctionChoiceBehaviorContext
{
    /// <summary>
    /// The <see cref="Kernel"/> to be used for function calling.
    /// </summary>
    public Kernel? Kernel { get; init; }
}
