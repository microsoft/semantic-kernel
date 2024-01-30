// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

public sealed class OllamaChatRequest
{
    /// <summary>
    /// Candidate responses from the model.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    [JsonPropertyName("messages'")]
    public ChatHistory? Messages { get; set; }

    /// <summary>
    /// Returns the text response data from LLM.
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; }

}
