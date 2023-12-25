#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

internal sealed class GeminiRequest
{
    public GeminiRequest(IEnumerable<GeminiRequestContent> contents)
    {
        this.Contents = contents;
    }

    [JsonPropertyName("contents")]
    public IEnumerable<GeminiRequestContent> Contents { get; set; }

    [JsonPropertyName("safetySettings")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IEnumerable<GeminiRequestSafetySetting>? SafetySettings { get; set; }

    [JsonPropertyName("generationConfig")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiRequestConfiguration? Configuration { get; set; }

    public static GeminiRequest FromPromptExecutionSettings(string prompt, GeminiPromptExecutionSettings executionSettings)
    {
        GeminiRequest obj = CreateGeminiRequest(prompt);
        AddSafetySettings(executionSettings, obj);
        AddConfiguration(executionSettings, obj);
        return obj;
    }

    private static GeminiRequest CreateGeminiRequest(string prompt)
    {
        GeminiRequest obj = new GeminiRequest(new[]
        {
            new GeminiRequestContent(parts: new[]
            {
                new GeminiRequestPart(text: prompt)
            })
        });
        return obj;
    }

    private static void AddConfiguration(GeminiPromptExecutionSettings executionSettings, GeminiRequest obj)
    {
        obj.Configuration = new GeminiRequestConfiguration
        {
            Temperature = executionSettings.Temperature,
            TopP = executionSettings.TopP,
            TopK = executionSettings.TopK,
            MaxOutputTokens = executionSettings.MaxTokens,
            StopSequences = executionSettings.StopSequences,
            CandidateCount = executionSettings.CandidateCount
        };
    }

    private static void AddSafetySettings(GeminiPromptExecutionSettings executionSettings, GeminiRequest obj)
    {
        if (executionSettings.SafetySettings is { Count: > 0 } safety)
        {
            obj.SafetySettings = safety.Select(s => new GeminiRequestSafetySetting(s.Category, s.Threshold));
        }
    }
}

internal sealed class GeminiRequestConfiguration
{
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature { get; set; }

    [JsonPropertyName("topP")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP { get; set; }

    [JsonPropertyName("topK")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopK { get; set; }

    [JsonPropertyName("maxOutputTokens")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxOutputTokens { get; set; }

    [JsonPropertyName("stopSequences")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IEnumerable<string>? StopSequences { get; set; }

    [JsonPropertyName("candidateCount")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? CandidateCount { get; set; }
}

internal sealed class GeminiRequestContent
{
    public GeminiRequestContent(IEnumerable<GeminiRequestPart> parts)
    {
        this.Parts = parts;
    }

    [JsonPropertyName("parts")]
    public IEnumerable<GeminiRequestPart> Parts { get; set; }

    [JsonPropertyName("role")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Role { get; set; }
}

internal sealed class GeminiRequestPart
{
    public GeminiRequestPart(string text)
    {
        this.Text = text;
    }

    [JsonPropertyName("text")]
    public string Text { get; set; }
}

internal sealed class GeminiRequestSafetySetting
{
    public GeminiRequestSafetySetting(string category, string threshold)
    {
        this.Category = category;
        this.Threshold = threshold;
    }

    [JsonPropertyName("category")]
    public string Category { get; set; }

    [JsonPropertyName("threshold")]
    public string Threshold { get; set; }
}
