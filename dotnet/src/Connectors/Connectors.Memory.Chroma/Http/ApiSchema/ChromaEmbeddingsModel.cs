// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

public class ChromaEmbeddingsModel
{
    [JsonPropertyName("ids")]
    public List<string>? Ids { get; set; }

    [JsonPropertyName("embeddings")]
    public List<float[]>? Embeddings { get; set; }

    [JsonPropertyName("metadatas")]
    public List<Dictionary<string, object>>? Metadatas { get; set; }
}
