// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// A record structure used by Qdrant that contains an embedding and metadata.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
public class QdrantVectorRecord
{
    /// <summary>
    /// The unique point id for assigned to the vector index.
    /// </summary>
    [JsonIgnore]
    public string PointId { get; }

    /// <summary>
    /// The embedding data.
    /// </summary>
    [JsonPropertyName("embedding")]
    public ReadOnlyMemory<float> Embedding { get; }

    /// <summary>
    /// The metadata.
    /// </summary>
    [JsonPropertyName("payload")]
    public Dictionary<string, object> Payload { get; }

    /// <summary>
    /// The tags used for search.
    /// </summary>
    [JsonPropertyName("tags")]
    public List<string>? Tags { get; }

    /// <summary>
    /// Constructor.
    /// </summary>
    /// <param name="pointId"></param>
    /// <param name="embedding"></param>
    /// <param name="payload"></param>
    /// <param name="tags"></param>
    public QdrantVectorRecord(string pointId, ReadOnlyMemory<float> embedding, Dictionary<string, object> payload, List<string>? tags = null)
    {
        this.PointId = pointId;
        this.Embedding = embedding;
        this.Payload = payload;
        this.Tags = tags;
    }

    /// <summary>
    /// Serializes the metadata to JSON.
    /// </summary>
    /// <returns>Serialized payload</returns>
    public string GetSerializedPayload()
    {
        return JsonSerializer.Serialize(this.Payload);
    }

    /// <summary>
    /// Deserializes the metadata from JSON.
    /// </summary>
    /// <param name="pointId"></param>
    /// <param name="embedding"></param>
    /// <param name="json"></param>
    /// <param name="tags"></param>
    /// <returns>Vector record</returns>
    /// <exception cref="KernelException">Qdrant exception</exception>
    public static QdrantVectorRecord FromJsonMetadata(string pointId, ReadOnlyMemory<float> embedding, string json, List<string>? tags = null)
    {
        var payload = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
        if (payload is not null)
        {
            return new QdrantVectorRecord(pointId, embedding, payload, tags);
        }

        throw new KernelException("Unable to deserialize record payload");
    }
}
