// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// A class for describing the reponse/return type of an SKFunction in a JSON Schema friendly way.
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
