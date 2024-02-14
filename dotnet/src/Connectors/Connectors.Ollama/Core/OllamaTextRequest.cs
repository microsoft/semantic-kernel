// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Response object model.
/// </summary>
public sealed class OllamaTextRequest
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

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="OllamaTextRequest" /> object.
    /// </summary>
    /// <param name="prompt">Prompt to be used for the request.</param>
    /// <param name="ollamaPromptExecutionSettings">Execution settings to be used for the request.</param>
    /// <returns>OllamaTextRequest object.</returns>
    public static OllamaTextRequest FromPromptAndExecutionSettings(string prompt, OllamaPromptExecutionSettings ollamaPromptExecutionSettings)
    {
        return new OllamaTextRequest
        {
            Model = ollamaPromptExecutionSettings.ModelId,
            Stream = false,
            Prompt = prompt
        };
    }
}
