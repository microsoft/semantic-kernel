// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama chat request object.
/// </summary>
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

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="OllamaChatRequest" /> object.
    /// </summary>
    /// <param name="chatHistory">Chat history to be used for the request.</param>
    /// <param name="ollamaPromptExecutionSettings">Execution settings to be used for the request.</param>
    /// <returns>OllamaChatRequest object.</returns>
    public static OllamaChatRequest FromPromptAndExecutionSettings(ChatHistory chatHistory, OllamaPromptExecutionSettings ollamaPromptExecutionSettings)
    {
        return new OllamaChatRequest
        {
            Model = ollamaPromptExecutionSettings.ModelId,
            Stream = false,
            Messages = chatHistory
        };
    }
}
