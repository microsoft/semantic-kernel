// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

/// <summary>
/// Chroma embeddings model.
/// </summary>
public class ChromaEmbeddingsModel
{
    /// <summary>
    /// Embedding identifiers.
    /// </summary>
    [JsonPropertyName("ids")]
    public List<string> Ids { get; set; } = new();

    /// <summary>
    /// Embedding vectors.
    /// </summary>
    [JsonPropertyName("embeddings")]
    public List<float[]> Embeddings { get; set; } = new();

    /// <summary>
    /// Embedding metadatas.
    /// </summary>
    [JsonPropertyName("metadatas")]
    public List<Dictionary<string, object>> Metadatas { get; set; } = new();
}
