// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

public sealed class EmbeddingResponse
{
    public sealed class EmbeddingVector
    {
        [JsonPropertyName("embedding")]
        public IList<float>? Embedding { get; set; }
    }

    [JsonPropertyName("data")]
    public IList<EmbeddingVector>? Embeddings { get; set; }
}
