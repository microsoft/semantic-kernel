// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.HuggingFace.HttpSchema;

/// <summary>
/// HTTP schema to perform embedding request.
/// </summary>
[Serializable]
public sealed class EmbeddingRequest
{
    /// <summary>
    /// Data to embed.
    /// </summary>
    [JsonPropertyName("inputs")]
    public IList<string> Input { get; set; } = new List<string>();
}
