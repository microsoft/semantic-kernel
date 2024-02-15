// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

#pragma warning disable CA1812

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Chat Response object model.
/// </summary>
internal sealed class OllamaChatResponse : OllamaResponseBase
{
    /// <summary>
    /// Message returned by the model.
    /// </summary>
    [JsonPropertyName("message")]
    public OllamaChatResponseMessage? Message { get; set; }

    internal sealed class OllamaChatResponseMessage
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }
}
