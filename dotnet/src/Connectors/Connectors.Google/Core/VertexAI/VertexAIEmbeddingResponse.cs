// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbeddingResponse
{
    [JsonPropertyName("predictions")]
    [JsonRequired]
    public IList<ResponsePrediction> Predictions { get; set; } = null!;

    internal sealed class ResponsePrediction
    {
        [JsonPropertyName("embeddings")]
        [JsonRequired]
        public ResponseEmbedding Embeddings { get; set; } = null!;

        internal sealed class ResponseEmbedding
        {
            [JsonPropertyName("values")]
            [JsonRequired]
            public ReadOnlyMemory<float> Values { get; set; }
        }
    }
}
