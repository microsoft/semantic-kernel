// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
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
    [JsonPropertyName("messages")]
    public IList<OllamaChatRequestMessage>? Messages { get; set; }

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
    /// <param name="connectorModelId">Model Id to be used for the request if no one is provided in the execution settings.</param>
    /// <returns>OllamaChatRequest object.</returns>
    internal static OllamaChatRequest FromPromptAndExecutionSettings(ChatHistory chatHistory, OllamaPromptExecutionSettings ollamaPromptExecutionSettings, string connectorModelId)
    {
        return new OllamaChatRequest
        {
            Model = ollamaPromptExecutionSettings.ModelId ?? connectorModelId,
            Stream = false,
            Messages = chatHistory.Select(message => new OllamaChatRequestMessage
            {
                Role = message.Role.ToString(),
                Content = message.Content
            }).ToList()
        };
    }

    public sealed class OllamaChatRequestMessage
    {
        /// <summary>
        /// Role of the message.
        /// </summary>
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        /// <summary>
        /// Content of the message.
        /// </summary>
        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }
}
