// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

#pragma warning disable CA1812

internal sealed class OllamaEmbeddingResponse : OllamaResponseBase
{
    /// <summary>
    /// Returns the text response data from LLM.
    /// </summary>
    [JsonPropertyName("embedding")]
    public float[]? Embedding { get; set; }
}
