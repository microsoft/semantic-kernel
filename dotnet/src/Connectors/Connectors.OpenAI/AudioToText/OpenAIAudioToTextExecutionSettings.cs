// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for an OpenAI audio-to-text request.
/// </summary>
public class OpenAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    [JsonPropertyName("filename")]
    public string Filename { get; set; }

    [JsonPropertyName("language")]
    public string? Language { get; set; }

    [JsonPropertyName("prompt")]
    public string? Prompt { get; set; }

    [JsonPropertyName("response_format")]
    public string ResponseFormat { get; set; } = "text";

    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }

    public OpenAIAudioToTextExecutionSettings(string filename)
    {
        this.Filename = filename;
    }

    public static OpenAIAudioToTextExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
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
