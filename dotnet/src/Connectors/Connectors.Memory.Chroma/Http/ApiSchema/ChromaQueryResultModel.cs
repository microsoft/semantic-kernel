// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

/// <summary>
/// Chroma query result model. Contains result sets after search operation.
/// </summary>
public class ChromaQueryResultModel
{
    /// <summary>
    /// List of embedding identifiers.
    /// </summary>
    [JsonPropertyName("ids")]
    public List<List<string>> Ids { get; set; } = new();

    /// <summary>
    /// List of embedding vectors.
    /// </summary>
    [JsonPropertyName("embeddings")]
    public List<List<float[]>> Embeddings { get; set; } = new();

    /// <summary>
    /// List of embedding metadatas.
    /// </summary>
    [JsonPropertyName("metadatas")]
    public List<List<Dictionary<string, object>>> Metadatas { get; set; } = new();

    /// <summary>
    /// List of embedding distances.
    /// </summary>
    [JsonPropertyName("distances")]
    public List<List<double>> Distances { get; set; } = new();
}
