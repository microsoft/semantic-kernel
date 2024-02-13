// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Text;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Execution Settings.
/// </summary>
public sealed class OllamaPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    public static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Gets the specialization for the Ollama execution settings.
    /// </summary>
    /// <param name="executionSettings">Generic prompt execution settings.</param>
    /// <returns>Specialized Ollama execution settings.</returns>
    public static OllamaPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new OllamaPromptExecutionSettings() { MaxTokens = DefaultTextMaxTokens };
            case OllamaPromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var ollamaExecutionSettings = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (ollamaExecutionSettings is not null)
        {
            return ollamaExecutionSettings;
        }

        throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(OllamaPromptExecutionSettings)}",
            nameof(executionSettings));
    }

    /// <summary>
    /// Maximum number of tokens to generate.
    /// </summary>
    public int? MaxTokens { get; set; }
}
