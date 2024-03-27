// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class GoogleAIEmbeddingResponse
{
    [JsonPropertyName("embeddings")]
    [JsonRequired]
    public IList<EmbeddingsValues> Embeddings { get; set; } = null!;

    internal sealed class EmbeddingsValues
    {
        [JsonPropertyName("values")]
        [JsonRequired]
        public ReadOnlyMemory<float> Values { get; set; }
    }
}
