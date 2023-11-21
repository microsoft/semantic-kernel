// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// A class to describe the parameters of an SKFunctionFactory in a JSON Schema friendly way.
/// </summary>
internal sealed class JsonSchemaFunctionParameters
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
    /// A dictionary of properties name => JSON Schema.
    /// </summary>
    [JsonPropertyName("properties")]
    public Dictionary<string, SKJsonSchema> Properties { get; set; } = new Dictionary<string, SKJsonSchema>();
}
