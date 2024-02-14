// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for OpenAI audio-to-text request.
/// </summary>
public sealed class OpenAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Filename or identifier associated with audio data.
    /// Should be in format {filename}.{extension}
    /// </summary>
    [JsonPropertyName("filename")]
    public string Filename { get; set; }

    /// <summary>
    /// An optional language of the audio data as two-letter ISO-639-1 language code (e.g. 'en' or 'es').
    /// </summary>
    [JsonPropertyName("language")]
    public string? Language { get; set; }

    /// <summary>
    /// An optional text to guide the model's style or continue a previous audio segment. The prompt should match the audio language.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string? Prompt { get; set; }

    /// <summary>
    /// The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt. Default is 'json'.
    /// </summary>
    [JsonPropertyName("response_format")]
    public string ResponseFormat { get; set; } = "json";

    /// <summary>
    /// The sampling temperature, between 0 and 1.
    /// Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    /// If set to 0, the model will use log probability to automatically increase the temperature until certain thresholds are hit.
    /// Default is 0.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float Temperature { get; set; } = 0;

    /// <summary>
    /// Creates an instance of <see cref="OpenAIAudioToTextExecutionSettings"/> class.
    /// </summary>
    /// <param name="filename">Filename or identifier associated with audio data. Should be in format {filename}.{extension}</param>
    public OpenAIAudioToTextExecutionSettings(string filename)
    {
        this.Filename = filename;
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="OpenAIAudioToTextExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="OpenAIAudioToTextExecutionSettings"/>.</returns>
    public static OpenAIAudioToTextExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is OpenAIAudioToTextExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAIAudioToTextExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        if (openAIExecutionSettings is not null)
        {
            return openAIExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(OpenAIAudioToTextExecutionSettings)}", nameof(executionSettings));
    }
}
