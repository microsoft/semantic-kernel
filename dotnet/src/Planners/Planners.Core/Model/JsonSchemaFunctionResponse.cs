// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planners.Model;

/// <summary>
/// A class for describing the reponse/return type of an SKFunction in a Json Schema friendly way.
/// </summary>
public sealed class JsonSchemaFunctionResponse
{
    /// <summary>
    /// The response description.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// The response content.
    /// </summary>
    [JsonPropertyName("content")]
    public JsonSchemaFunctionContent Content { get; set; } = new JsonSchemaFunctionContent();
}
