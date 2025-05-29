// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents an input for an agent.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AgentInput
{
    /// <summary>
    /// Gets or sets the type of the input.
    /// </summary>
    /// <remarks>
    /// This can be either a string, number, array, object, or boolean.
    /// </remarks>
    public string? Type { get; set; }

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
    public string? JsonSchema { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the input can contain structural text.
    /// </summary>
    /// <remarks>
    /// The default is true.
    /// When set to false the value of the input is treated as safe content i.e. the input can emit structural text.
    /// </remarks>
    public bool Strict { get; set; } = true;

    /// <summary>
    /// Gets or sets a sample value for the input.
    /// </summary>
    /// <remarks>
    /// This is used to provide examples to the user of the agent.
    /// This can also be used by developer tooling as the value to use without needing to prompt the developer to enter a value.
    /// </remarks>
    public object? Sample { get; set; }
}
