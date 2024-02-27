// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

internal sealed class GeminiRequest
{
    [JsonPropertyName("contents")]
    public IList<GeminiContent> Contents { get; set; } = null!;

    [JsonPropertyName("safetySettings")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<GeminiSafetySetting>? SafetySettings { get; set; }

    [JsonPropertyName("generationConfig")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public ConfigurationElement? Configuration { get; set; }

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
            Contents = new List<GeminiContent>
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
            Contents = chatHistory.Select(c => new GeminiContent
            {
                Parts = CreateGeminiParts(c),
                Role = c.Role
            }).ToList()
        };
        return obj;
    }

    private static List<GeminiPart> CreateGeminiParts(ChatMessageContent content)
    {
        var list = content.Items?.Select(item => item switch
        {
            TextContent textContent => new GeminiPart { Text = textContent.Text },
            ImageContent imageContent => CreateGeminiPartFromImage(imageContent),
            _ => throw new NotSupportedException($"Unsupported content type. {item.GetType().Name} is not supported by Gemini.")
        }).ToList() ?? new List<GeminiPart>();

        if (list.Count == 0)
        {
            list.Add(new GeminiPart { Text = content.Content ?? string.Empty });
        }

        return list;
    }

    private static GeminiPart CreateGeminiPartFromImage(ImageContent imageContent)
    {
        // Binary data takes precedence over URI as per the ImageContent.ToString() implementation.
        if (imageContent.Data is { IsEmpty: false })
        {
            return new GeminiPart
            {
                InlineData = new GeminiPart.InlineDataPart
                {
                    MimeType = GetMimeTypeFromImageContentDataMediaType(imageContent),
                    InlineData = Convert.ToBase64String(imageContent.Data.ToArray())
                }
            };
        }

        if (imageContent.Uri is not null)
        {
            return new GeminiPart
            {
                FileData = new GeminiPart.FileDataPart
                {
                    MimeType = GetMimeTypeFromImageContentMetadata(imageContent),
                    FileUri = imageContent.Uri ?? throw new InvalidOperationException("Image content URI is empty.")
                }
            };
        }

        throw new InvalidOperationException("Image content does not contain any data or uri.");
    }

    private static string GetMimeTypeFromImageContentDataMediaType(ImageContent imageContent)
    {
        return imageContent.Data?.MediaType
               ?? throw new InvalidOperationException("Image content Data.MediaType is empty.");
    }

    private static string GetMimeTypeFromImageContentMetadata(ImageContent imageContent)
    {
        var key = imageContent.Metadata?.Keys.SingleOrDefault(key =>
                      key.Equals("mimeType", StringComparison.OrdinalIgnoreCase)
                      || key.Equals("mime_type", StringComparison.OrdinalIgnoreCase))
                  ?? throw new InvalidOperationException("Mime type is not found in the image content metadata.");
        return imageContent.Metadata[key]!.ToString();
    }

    private static void AddConfiguration(GeminiPromptExecutionSettings executionSettings, GeminiRequest obj)
    {
        obj.Configuration = new ConfigurationElement
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

    internal sealed class ConfigurationElement
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
}
