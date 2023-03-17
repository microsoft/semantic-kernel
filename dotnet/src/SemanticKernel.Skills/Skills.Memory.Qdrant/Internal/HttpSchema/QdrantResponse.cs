// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal abstract class QdrantResponse<TResponse> 
    where TResponse : class
{
    /// <summary>
    /// Response class type: TResponse ex. CollectionData, Points
    /// </summary>
    public TResponse Response { get; set; } = default!;
    
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
