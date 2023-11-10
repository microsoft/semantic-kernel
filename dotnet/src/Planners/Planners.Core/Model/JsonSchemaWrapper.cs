// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Planners.Model;

/// <summary>
/// A class to describe the content schma of a response/return type from an SKFunction, in a Json Schema friendly way.
/// </summary>
public sealed class JsonSchemaWrapper
{
    /// <summary>
    /// The Json Schema
    /// </summary>
    [JsonPropertyName("schema")]
    public JsonDocument? Schema { get; set; }
}
