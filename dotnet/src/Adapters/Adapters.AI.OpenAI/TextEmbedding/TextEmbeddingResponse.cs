// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

/// <summary>
/// A response from an embedding request
/// </summary>
public sealed class TextEmbeddingResponse
{
    /// <summary>
    /// A single embedding vector
    /// </summary>
    public sealed class EmbeddingResponseIndex
    {
        /// <summary>
        /// The embedding vector
        /// </summary>
        [JsonPropertyName("embedding")]
        public IList<float> Values { get; set; } = new List<float>();

        /// <summary>
        /// Index of the embedding vector
        /// </summary>
        [JsonPropertyName("index")]
        public int Index { get; set; }
    }

    /// <summary>
    /// A list of embeddings
    /// </summary>
    [JsonPropertyName("data")]
    public IList<EmbeddingResponseIndex> Embeddings { get; set; } = new List<EmbeddingResponseIndex>();
}
