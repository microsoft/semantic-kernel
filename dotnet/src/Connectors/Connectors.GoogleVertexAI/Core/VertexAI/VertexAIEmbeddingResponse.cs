// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.VertexAI;

internal sealed class VertexAIEmbeddingResponse
{
    [JsonPropertyName("predictions")]
    public IList<VertexAIEmbeddingResponsePrediction> Predictions { get; set; } = null!;
}

internal sealed class VertexAIEmbeddingResponsePrediction
{
    [JsonPropertyName("embeddings")]
    public VertexAIEmbeddingResponseEmbedding Embeddings { get; set; } = null!;
}

internal sealed class VertexAIEmbeddingResponseEmbedding
{
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }
}
