// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// HTTP schema to perform embedding request.
/// </summary>
internal sealed class TextEmbeddingRequest
{
    /// <summary>
    /// Data to embed.
    /// </summary>
    [JsonPropertyName("inputs")]
    public IList<string> Inputs { get; set; } = [];
}
