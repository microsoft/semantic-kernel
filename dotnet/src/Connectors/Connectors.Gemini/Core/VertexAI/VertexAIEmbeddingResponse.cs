#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.GoogleAI;

internal sealed class VertexAIEmbeddingResponse
{
    [JsonPropertyName("predictions")]
    public IList<VertexAIEmbeddingResponsePrediction> Predictions { get; set; }
}

internal sealed class VertexAIEmbeddingResponsePrediction
{
    [JsonPropertyName("embeddings")]
    public VertexAIEmbeddingResponseEmbedding Embeddings { get; set; }
}

internal sealed class VertexAIEmbeddingResponseEmbedding
{
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }
}
