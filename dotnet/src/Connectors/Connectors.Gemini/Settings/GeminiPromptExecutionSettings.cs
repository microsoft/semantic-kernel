#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Settings;

/// <summary>
/// Represents the settings for executing a prompt with the Gemini model.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class GeminiPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Default max tokens for a text generation
    /// </summary>
    internal static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Default is 1.0.
    /// </summary>
    public double Temperature { get; set; } = 1;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// Default is 0.95.
    /// </summary>
    public double TopP { get; set; } = 0.95;

    /// <summary>
    /// Gets or sets the value of the TopK property.
    /// The TopK property represents the maximum value of a collection or dataset.
    /// The default value is 50.
    /// </summary>
    public double TopK { get; set; } = 50;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string>? StopSequences { get; set; }

    /// <summary>
    /// Represents a list of safety settings.
    /// </summary>
    public IList<SafetySetting>? SafetySettings { get; set; }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings"/> object to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// </summary>
    /// <param name="executionSettings">The <see cref="PromptExecutionSettings"/> object to convert.</param>
    /// <returns>
    /// The converted <see cref="GeminiPromptExecutionSettings"/> object. If <paramref name="executionSettings"/> is null,
    /// a new instance of <see cref="GeminiPromptExecutionSettings"/> is returned. If <paramref name="executionSettings"/>
    /// is already a <see cref="GeminiPromptExecutionSettings"/> object, it is casted and returned. Otherwise, the method
    /// tries to deserialize <paramref name="executionSettings"/> to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// If deserialization is successful, the converted object is returned. If deserialization fails or the converted object
    /// is null, an <see cref="ArgumentException"/> is thrown.
    /// </returns>
    public static GeminiPromptExecutionSettings FromPromptExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new GeminiPromptExecutionSettings() { MaxTokens = DefaultTextMaxTokens };
        }

        if (executionSettings is GeminiPromptExecutionSettings)
        {
            return (GeminiPromptExecutionSettings)executionSettings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var geminiExecutionSettings = JsonSerializer.Deserialize<GeminiPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (geminiExecutionSettings is not null)
        {
            return geminiExecutionSettings;
        }

        throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(GeminiPromptExecutionSettings)}",
            nameof(executionSettings));
    }
}
