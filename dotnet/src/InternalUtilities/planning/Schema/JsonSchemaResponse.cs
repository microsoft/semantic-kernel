// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class to describe the content schma of a response/return type from an KernelFunctionFactory, in a JSON Schema friendly way.
/// </summary>
internal sealed class JsonSchemaResponse
{
    /// <summary>
    /// The JSON Schema
    /// </summary>
    [JsonPropertyName("schema")]
    public KernelJsonSchema? Schema { get; set; }
}
