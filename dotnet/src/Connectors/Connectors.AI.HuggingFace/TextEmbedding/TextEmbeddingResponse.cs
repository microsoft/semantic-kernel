// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

/// <summary>
/// HTTP Schema for embedding response.
/// </summary>
public sealed class TextEmbeddingResponse
{
    /// <summary>
    /// Model containing embedding.
    /// </summary>
    public sealed class EmbeddingVector
    {
        [JsonPropertyName("embedding")]
        [JsonConverter(typeof(ReadOnlyMemoryConverter))]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    /// <summary>
    /// List of embeddings.
    /// </summary>
    [JsonPropertyName("data")]
    public IList<EmbeddingVector>? Embeddings { get; set; }
}
