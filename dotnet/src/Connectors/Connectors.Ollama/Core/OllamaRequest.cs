// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Response object model.
/// </summary>
public sealed class OllamaRequest
{
    /// <summary>
    /// Candidate responses from the model.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    [JsonPropertyName("prompt'")]
    public string? Prompt { get; set; }

    /// <summary>
    /// Returns the text response data from LLM.
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; }

    public static OllamaRequest FromPromptAndExecutionSettings(ChatHistory chatHistory, OllamaExecutionSettings ollamaExecutionSettings)
    {
        throw new System.NotImplementedException();
    }
}
