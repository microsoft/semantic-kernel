// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.PaLM.TextEmbedding;

/*
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
        public IList<float>? Embedding { get; set; }
    }

    /// <summary>
    /// List of embeddings.
    /// </summary>
    [JsonPropertyName("data")]
    public IList<EmbeddingVector>? Embeddings { get; set; }
}
*/
public class Embedding
{
    public List<float> value { get; set; }
}

public sealed class TextEmbeddingResponse
{
    public Embedding embedding { get; set; }
}