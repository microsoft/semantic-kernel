// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Planners.Model;

/// <summary>
/// A class to describe the parameters of an SKFunction in a Json Schema friendly way.
/// </summary>
public sealed class JsonSchemaFunctionParameters
{
    /// <summary>
    /// The type of schema which is always "object" when describing function parameters.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type => "object";

    /// <summary>
    /// The list of required properties.
    /// </summary>
    [JsonPropertyName("required")]
    public List<string> Required { get; set; } = new List<string>();

    /// <summary>
    /// A dictionary of properties name => Json Schema.
    /// </summary>

    [JsonPropertyName("properties")]
    public Dictionary<string, JsonDocument> Properties { get; set; } = new Dictionary<string, JsonDocument>();
}
