// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

/// <summary>
/// Base class for Qdrant response schema.
/// </summary>
internal abstract class QdrantResponse
{
    /// <summary>
    /// Response status
    /// </summary>
    [JsonPropertyName("status")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Status { get; set; }

    /// <summary>
    /// Response time
    /// </summary>
    [JsonPropertyName("time")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Time { get; set; }
}
