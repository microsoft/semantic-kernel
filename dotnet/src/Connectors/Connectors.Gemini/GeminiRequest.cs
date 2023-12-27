#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

// TODO: Add required attributes to non-nullable properties after updating solution to C# 12.0

public sealed class GeminiRequest
{
    [JsonPropertyName("contents")]
    public IList<GeminiRequestContent> Contents { get; set; }

    [JsonPropertyName("safetySettings")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<GeminiRequestSafetySetting>? SafetySettings { get; set; }

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
        GeminiRequest obj = new()
        {
            Contents = new List<GeminiRequestContent>
            {
                new()
                {
                    Parts = new List<GeminiRequestPart>
                    {
                        new()
                        {
                            Text = prompt
                        }
                    }
                }
            }
        };
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
        obj.SafetySettings = executionSettings.SafetySettings?.Select(s => new GeminiRequestSafetySetting
        {
            Category = s.Category,
            Threshold = s.Threshold
        }).ToList();
    }
}

public sealed class GeminiRequestConfiguration
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

public sealed class GeminiRequestContent
{
    [JsonPropertyName("parts")]
    public IList<GeminiRequestPart> Parts { get; set; }

    [JsonPropertyName("role")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Role { get; set; }
}

public sealed class GeminiRequestPart
{
    [JsonPropertyName("text")]
    public string Text { get; set; }
}

public sealed class GeminiRequestSafetySetting
{
    [JsonPropertyName("category")]
    public string Category { get; set; }

    [JsonPropertyName("threshold")]
    public string Threshold { get; set; }
}
