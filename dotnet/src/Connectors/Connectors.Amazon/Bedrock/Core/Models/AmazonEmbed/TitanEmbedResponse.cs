// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// The Amazon Titan Embed response object when deserialized from Invoke Model call.
/// </summary>
internal sealed class TitanTextEmbeddingResponse
{
    /// <summary>
    /// The number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }

    /// <summary>
    /// The float array of the embedding.
    /// </summary>
    [JsonPropertyName("embedding")]
    public ReadOnlyMemory<float> Embedding { get; set; }
}
