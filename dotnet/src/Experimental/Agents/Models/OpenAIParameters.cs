// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// Wrapper for parameter map.
/// </summary>
internal sealed class OpenAIParameters
{
    /// <summary>
    /// Empty parameter set.
    /// </summary>
    public static readonly OpenAIParameters Empty = new();

    /// <summary>
    /// Always "object"
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = "object";

    /// <summary>
    /// Set of parameters.
    /// </summary>
    [JsonPropertyName("properties")]
    public Dictionary<string, OpenAIParameter> Properties { get; set; } = new();

    /// <summary>
    /// Set of parameters.
    /// </summary>
    [JsonPropertyName("required")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? Required { get; set; }
}

/// <summary>
/// Wrapper for parameter definition.
/// </summary>
internal sealed class OpenAIParameter
{
    /// <summary>
    /// The parameter type.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = "object";

    /// <summary>
    /// The parameter description.
    /// </summary>
    [JsonPropertyName("description")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; set; }
}
