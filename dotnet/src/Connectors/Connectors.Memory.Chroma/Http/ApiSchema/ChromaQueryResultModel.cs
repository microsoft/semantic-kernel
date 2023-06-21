// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
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
    public List<List<string>>? CollectionIds { get; set; }

    /// <summary>
    /// List of embedding vectors.
    /// </summary>
    [JsonPropertyName("embeddings")]
    public List<List<float[]>>? CollectionEmbeddings { get; set; }

    /// <summary>
    /// List of embedding metadatas.
    /// </summary>
    [JsonPropertyName("metadatas")]
    public List<List<Dictionary<string, object>>>? CollectionMetadatas { get; set; }

    /// <summary>
    /// List of embedding distances.
    /// </summary>
    [JsonPropertyName("distances")]
    public List<List<double>>? CollectionDistances { get; set; }

    /// <summary>
    /// Embedding identifiers.
    /// </summary>
    [JsonIgnore]
    public List<string>? Ids => this.CollectionIds?.FirstOrDefault();

    /// <summary>
    /// Embedding vectors.
    /// </summary>
    [JsonIgnore]
    public List<float[]>? Embeddings => this.CollectionEmbeddings?.FirstOrDefault();

    /// <summary>
    /// Embedding metadatas.
    /// </summary>
    [JsonIgnore]
    public List<Dictionary<string, object>>? Metadatas => this.CollectionMetadatas?.FirstOrDefault();

    /// <summary>
    /// Embedding distances.
    /// </summary>
    [JsonIgnore]
    public List<double>? Distances => this.CollectionDistances?.FirstOrDefault();
}
