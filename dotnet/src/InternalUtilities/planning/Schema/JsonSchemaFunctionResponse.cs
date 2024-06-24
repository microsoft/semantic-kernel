// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class for describing the reponse/return type of an KernelFunctionFactory in a JSON Schema friendly way.
/// </summary>
internal sealed class JsonSchemaFunctionResponse
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
