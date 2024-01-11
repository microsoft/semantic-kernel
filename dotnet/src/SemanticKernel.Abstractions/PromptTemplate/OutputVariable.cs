// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an output variable returned from a prompt function.
/// </summary>
public sealed class OutputVariable
{
    /// <summary>The description of the variable.</summary>
    private string _description = string.Empty;

    /// <summary>
    /// Gets or sets a description of this output.
    /// </summary>
    [JsonPropertyName("description")]
    [AllowNull]
    public string Description
    {
        get => this._description;
        set => this._description = value ?? string.Empty;
    }

    /// <summary>
    /// Gets or sets JSON Schema describing this output.
    /// </summary>
    /// <remarks>
    /// This string will be deserialized into an instance of <see cref="KernelJsonSchema"/>.
    /// </remarks>
    [JsonPropertyName("json_schema")]
    public string? JsonSchema { get; set; }
}
