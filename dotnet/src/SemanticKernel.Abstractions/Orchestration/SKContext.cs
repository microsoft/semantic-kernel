// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel context.
/// </summary>
public sealed class SKContext
{
    /// <summary>
    /// User variables
    /// </summary>
    public ContextVariables Variables { get; }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="variables">Context variables to include in context.</param>
    internal SKContext(
        ContextVariables? variables = null)
    {
        this.Variables = variables ?? new();
    }

    /// <summary>
    /// Create a clone of the current context, using the same kernel references (memory, plugins, logger)
    /// and a new set variables, so that variables can be modified without affecting the original context.
    /// </summary>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone()
        => this.Clone(null);

    /// <summary>
    /// Create a clone of the current context, using the same kernel references (memory, plugins, logger)
    /// and optionally allows overriding the variables and plugins.
    /// </summary>
    /// <param name="variables">Override the variables with the provided ones</param>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone(ContextVariables? variables)
    {
        return new SKContext(
            variables ?? this.Variables.Clone());
    }
}
