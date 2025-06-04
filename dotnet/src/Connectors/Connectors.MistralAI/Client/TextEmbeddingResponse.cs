// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Response for text embedding.
/// </summary>
internal sealed class TextEmbeddingResponse : MistralResponseBase
{
    [JsonPropertyName("data")]
    public IList<MistralEmbedding>? Data { get; set; }
}
