// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for OpenAI text-to-audio request.
/// </summary>
public sealed class OpenAITextToAudioExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// The voice to use when generating the audio. Supported voices are alloy, echo, fable, onyx, nova, and shimmer.
    /// </summary>
    [JsonPropertyName("voice")]
    public string Voice { get; set; }

    /// <summary>
    /// The format to audio in. Supported formats are mp3, opus, aac, and flac.
    /// </summary>
    [JsonPropertyName("response_format")]
    public string ResponseFormat { get; set; } = "mp3";

    /// <summary>
    /// The speed of the generated audio. Select a value from 0.25 to 4.0. 1.0 is the default.
    /// </summary>
    [JsonPropertyName("speed")]
    public float Speed { get; set; } = 1.0f;

    /// <summary>
    /// Creates an instance of <see cref="OpenAITextToAudioExecutionSettings"/> class.
    /// </summary>
    /// <param name="voice">The voice to use when generating the audio. Supported voices are alloy, echo, fable, onyx, nova, and shimmer.</param>
    public OpenAITextToAudioExecutionSettings(string voice)
    {
        this.Voice = voice;
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="OpenAITextToAudioExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="OpenAITextToAudioExecutionSettings"/>.</returns>
    public static OpenAITextToAudioExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is OpenAITextToAudioExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAITextToAudioExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        if (openAIExecutionSettings is not null)
        {
            return openAIExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(OpenAITextToAudioExecutionSettings)}", nameof(executionSettings));
    }
}
