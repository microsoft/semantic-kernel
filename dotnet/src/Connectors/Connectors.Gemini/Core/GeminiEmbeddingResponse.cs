#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

internal sealed class GeminiEmbeddingResponse
{
    [JsonPropertyName("embeddings")]
    public GeminiEmbeddingResponseValues[] Embeddings { get; set; }
}

internal sealed class GeminiEmbeddingResponseValues
{
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }
}
