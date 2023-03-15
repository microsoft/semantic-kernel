// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

public class VectorRecordData<TEmbedding> : IEmbeddingWithMetadata<TEmbedding>
    where TEmbedding : unmanaged
{
    public Embedding<TEmbedding> Embedding { get; private set; }
    public Dictionary<string, object> Payload { get; set; }
    public List<string>? Tags { get; set; }

    public VectorRecordData(Embedding<TEmbedding> embedding, Dictionary<string, object> payload, List<string>? tags)
    {
        this.Embedding = embedding;
        this.Payload = payload;
        this.Tags = tags;
    }
}
