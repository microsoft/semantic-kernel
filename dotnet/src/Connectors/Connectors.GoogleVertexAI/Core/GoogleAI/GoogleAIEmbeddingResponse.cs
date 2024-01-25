// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

internal sealed class GoogleAIEmbeddingResponse
{
    [JsonPropertyName("embeddings")]
    [JsonRequired]
    public IList<GoogleAIEmbeddingResponseValues> Embeddings { get; set; } = null!;
}

internal sealed class GoogleAIEmbeddingResponseValues
{
    [JsonPropertyName("values")]
    [JsonRequired]
    public ReadOnlyMemory<float> Values { get; set; }
}
