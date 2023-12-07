// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Output variable return from a prompt functions.
/// </summary>
public sealed class OutputVariable
{
    /// <summary>
    /// Variable description for UI applications and planners. Localization is not supported here.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// JsonSchema describing this variable.
    /// </summary>
    /// <remarks>
    /// This string will be deserialised into an instance of <see cref="KernelJsonSchema"/>.
    /// </remarks>
    [JsonPropertyName("json_schema")]
    public string? JsonSchema { get; set; }
}
