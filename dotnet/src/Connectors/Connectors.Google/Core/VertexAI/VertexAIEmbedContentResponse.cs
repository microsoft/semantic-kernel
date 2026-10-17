// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbedContentResponse
{
    [JsonPropertyName("embedding")]
    [JsonRequired]
    public ResponseEmbedding Embedding { get; set; } = null!;

    internal sealed class ResponseEmbedding
    {
        [JsonPropertyName("values")]
        [JsonRequired]
        public ReadOnlyMemory<float> Values { get; set; }
    }
}
