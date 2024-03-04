// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Mistral embedding data.
/// </summary>
internal sealed class MistralEmbedding
{
    [JsonPropertyName("object")]
    public string? Object { get; set; }

    [JsonPropertyName("embedding")]
    public IList<float>? Embedding { get; set; }

    [JsonPropertyName("index")]
    public int? Index { get; set; }
}
