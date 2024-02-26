// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

internal sealed class OllamaEmbeddingResponse : OllamaResponseBase
{
    /// <summary>
    /// Returns the text response data from LLM.
    /// </summary>
    [JsonPropertyName("embedding")]
    public float[]? Embedding { get; set; }
}
