// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

public class ChromaQueryResultModel
{
    [JsonPropertyName("ids")]
    public List<List<string>>? CollectionIds { get; set; }

    [JsonPropertyName("embeddings")]
    public List<List<float[]>>? CollectionEmbeddings { get; set; }

    [JsonPropertyName("metadatas")]
    public List<List<Dictionary<string, object>>>? CollectionMetadatas { get; set; }

    [JsonPropertyName("distances")]
    public List<List<double>>? CollectionDistances { get; set; }

    [JsonIgnore]
    public List<string>? Ids => this.CollectionIds?.FirstOrDefault();

    [JsonIgnore]
    public List<float[]>? Embeddings => this.CollectionEmbeddings?.FirstOrDefault();

    [JsonIgnore]
    public List<Dictionary<string, object>>? Metadatas => this.CollectionMetadatas?.FirstOrDefault();

    [JsonIgnore]
    public List<double>? Distances => this.CollectionDistances?.FirstOrDefault();
}
