// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// A record structure used by Qdrant that contains an embedding and metadata.
/// </summary>
/// <typeparam name="TEmbedding"></typeparam>
public class QdrantVectorRecord<TEmbedding> : IEmbeddingWithMetadata<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// The embedding data.
    /// </summary>
    [JsonPropertyName("embedding")]
    public Embedding<TEmbedding> Embedding { get; private set; }

    /// <summary>
    /// The metadata.
    /// </summary>
    [JsonPropertyName("payload")]
    public Dictionary<string, object> Payload { get; private set; }

    /// <summary>
    /// The tags used for search.
    /// </summary>
    [JsonPropertyName("tags")]
    public List<string>? Tags { get; private set; }

    /// <summary>
    /// Constructor.
    /// </summary>
    /// <param name="embedding"></param>
    /// <param name="payload"></param>
    /// <param name="tags"></param>
    public QdrantVectorRecord(Embedding<TEmbedding> embedding, Dictionary<string, object> payload, List<string>? tags = null)
    {
        this.Embedding = embedding;
        this.Payload = payload;
        this.Tags = tags;
    }

    /// <summary>
    /// Serializes the metadata to JSON.
    /// </summary>
    /// <returns></returns>
    public string GetSerializedMetadata()
    {
        return JsonSerializer.Serialize(this.Payload);
    }

    /// <summary>
    /// Deserializes the metadata from JSON.
    /// </summary>
    /// <param name="embedding"></param>
    /// <param name="json"></param>
    /// <param name="tags"></param>
    /// <returns></returns>
    /// <exception cref="VectorDbException"></exception>
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types", Justification = "Following 'IsSupported' pattern of System.Numerics.")]
    public static QdrantVectorRecord<TEmbedding> FromJson(Embedding<TEmbedding> embedding, string json, List<string>? tags = null)
    {
        var payload = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
        if (payload != null)
        {
            return new QdrantVectorRecord<TEmbedding>(embedding, payload, tags);
        }
        else
        {
            throw new VectorDbException(VectorDbException.ErrorCodes.UnableToDeserializeRecordPayload, "Failed to deserialize payload");
        }
    }
}
