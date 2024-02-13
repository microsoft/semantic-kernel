// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

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
    internal ChatMessageContent? Message { get; set; }
}
