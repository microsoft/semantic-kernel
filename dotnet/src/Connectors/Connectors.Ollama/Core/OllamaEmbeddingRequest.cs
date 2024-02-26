// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

internal sealed class OllamaEmbeddingRequest
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
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="OllamaEmbeddingRequest" /> object.
    /// </summary>
    /// <param name="prompt">Prompt to be used for the request.</param>
    /// <param name="ollamaPromptExecutionSettings">Execution settings to be used for the request.</param>
    /// <param name="connectorModelId">Model Id to be used for the request if no one is provided in the execution settings.</param>
    /// <returns>OllamaTextRequest object.</returns>
    public static OllamaEmbeddingRequest FromPromptAndExecutionSettings(string prompt, OllamaPromptExecutionSettings ollamaPromptExecutionSettings, string connectorModelId)
    {
        return new OllamaEmbeddingRequest
        {
            Model = ollamaPromptExecutionSettings.ModelId ?? connectorModelId,
            Prompt = prompt
        };
    }
}
