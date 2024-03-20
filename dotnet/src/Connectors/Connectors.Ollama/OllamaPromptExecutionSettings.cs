// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

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
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens
    {
        get => this._maxTokens;

        set
        {
            this.ThrowIfFrozen();
            this._maxTokens = value;
        }
    }

    #region private ================================================================================

    private int? _maxTokens;

    #endregion
}
