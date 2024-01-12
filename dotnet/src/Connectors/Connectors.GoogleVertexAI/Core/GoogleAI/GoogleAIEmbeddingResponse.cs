#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.GoogleAI;

internal sealed class GoogleAIEmbeddingResponse
{
    [JsonPropertyName("embeddings")]
    public IList<GoogleAIEmbeddingResponseValues> Embeddings { get; set; } = null!;
}

internal sealed class GoogleAIEmbeddingResponseValues
{
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }
}
