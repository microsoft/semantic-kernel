// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

/// <summary>
/// HTTP schema to perform embedding request.
/// </summary>
[Serializable]
public sealed class TextEmbeddingRequest
{
    /// <summary>
    /// Data to embed.
    /// </summary>
    [JsonPropertyName("inputs")]
    public IList<string> Input { get; set; } = new List<string>();
}
