// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbedContentResponse
{
    [JsonPropertyName("embeddings")]
    [JsonRequired]
    public IList<ResponseEmbedding> Embeddings { get; set; } = null!;

    internal sealed class ResponseEmbedding
    {
        [JsonPropertyName("values")]
        [JsonRequired]
        public ReadOnlyMemory<float> Values { get; set; }
    }
}
