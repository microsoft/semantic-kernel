#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;

internal sealed class GeminiRequest
{
    [JsonPropertyName("contents")]
    public IList<GeminiRequestContent> Contents { get; set; }

    [JsonPropertyName("safetySettings")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<GeminiSafetySetting>? SafetySettings { get; set; }

    [JsonPropertyName("generationConfig")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiRequestConfiguration? Configuration { get; set; }

    /// <summary>
    /// Creates a <see cref="GeminiRequest"/> object from the given prompt and execution settings.
    /// </summary>
    /// <param name="prompt">The prompt to be assigned to the GeminiRequest.</param>
    /// <param name="executionSettings">The execution settings to be applied to the GeminiRequest.</param>
    /// <returns>A new instance of <see cref="GeminiRequest"/>.</returns>
    public static GeminiRequest FromPromptAndExecutionSettings(
        string prompt,
        GeminiPromptExecutionSettings executionSettings)
    {
        GeminiRequest obj = CreateGeminiRequest(prompt);
        AddSafetySettings(executionSettings, obj);
        AddConfiguration(executionSettings, obj);
        return obj;
    }

    public static GeminiRequest FromChatHistoryAndExecutionSettings(
        ChatHistory chatHistory,
        GeminiPromptExecutionSettings promptExecutionSettings)
    {
        GeminiRequest obj = CreateGeminiRequest(chatHistory);
        AddSafetySettings(promptExecutionSettings, obj);
        AddConfiguration(promptExecutionSettings, obj);
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
                    Parts = new List<GeminiPart>
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

    private static GeminiRequest CreateGeminiRequest(ChatHistory chatHistory)
    {
        GeminiRequest obj = new()
        {
            Contents = chatHistory.Select(c => new GeminiRequestContent
            {
                Parts = new List<GeminiPart>
                {
                    new()
                    {
                        Text = (c.Content ?? (c.Items?.SingleOrDefault(content => content is TextContent)
                            as TextContent)?.Text) ?? string.Empty,
                    }
                },
                Role = c.Role
            }).ToList()
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
        obj.SafetySettings = executionSettings.SafetySettings?.Select(s
            => new GeminiSafetySetting(s.Category, s.Threshold)).ToList();
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
    [JsonPropertyName("parts")]
    public IList<GeminiPart> Parts { get; set; }

    [JsonPropertyName("role")]
    [JsonConverter(typeof(AuthorRoleConverter))]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public AuthorRole? Role { get; set; }
}

internal sealed class GeminiRequestInlineData
{
    [JsonPropertyName("mimeType")]
    public string MimeType { get; set; }

    [JsonPropertyName("data")]
    public string Data { get; set; }
}
