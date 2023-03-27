// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

public class QdrantVectorRecord<TEmbedding> : IEmbeddingWithMetadata<TEmbedding>
    where TEmbedding : unmanaged
{
    public Embedding<TEmbedding> Embedding { get; private set; }
    public Dictionary<string, object> Payload { get; set; }
    public List<string>? Tags { get; set; }

    public QdrantVectorRecord(Embedding<TEmbedding> embedding, Dictionary<string, object> payload, List<string>? tags)
    {
        this.Embedding = embedding;
        this.Payload = payload;
        this.Tags = tags;
    }

    public string JsonSerializeMetadata()
    {
        return JsonSerializer.Serialize(this.Payload);
    }

    public static QdrantVectorRecord<TEmbedding> FromJson(Embedding<TEmbedding> embedding, string json, List<string>? tags = null)
    {
        var payload = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
        if (payload != null)
        {
            return new QdrantVectorRecord<TEmbedding>(embedding, payload, tags);
        }
        else
        {
            throw new VectorDbException(VectorDbException.ErrorCodes.UnableToSerializeRecordPayload, "Failed to deserialize payload");
        }
    }
}
