// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents an input for and agent.
/// </summary>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
public sealed class AgentInput
{
    /// <summary>
    /// Gets or sets the name of the input.
    /// </summary>
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets a description of the input.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets a default value for the input.
    /// </summary>
    public object? Default { get; set; }

    /// <summary>
    /// Gets or sets whether the input is considered required (rather than optional).
    /// </summary>
    /// <remarks>
    /// The default is true.
    /// </remarks>
    public bool Required { get; set; } = true;

    /// <summary>
    /// Gets or sets JSON Schema describing this input.
    /// </summary>
    public string? Schema { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether to handle the input value as potential dangerous content.
    /// </summary>
    /// <remarks>
    /// The default is true.
    /// When set to false the value of the input input is treated as safe content.
    /// </remarks>
    public bool Strict { get; set; } = true;

    /// <summary>
    /// Gets or sets a sample value for the input.
    /// </summary>
    public object? Sample { get; set; }
}
