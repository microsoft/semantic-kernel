// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

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

    [JsonPropertyName("tools")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<GeminiTool>? Tools { get; set; }

    public void AddFunction(GeminiFunction function)
    {
        // NOTE: Currently Gemini only supports one tool i.e. function calling.
        this.Tools ??= [];
        if (this.Tools.Count == 0)
        {
            this.Tools.Add(new GeminiTool());
        }

        this.Tools[0].Functions.Add(function.ToFunctionDeclaration());
    }

    /// <summary>
    /// Creates a <see cref="GeminiRequest"/> object from the given prompt and <see cref="GeminiPromptExecutionSettings"/>.
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

    /// <summary>
    /// Creates a <see cref="GeminiRequest"/> object from the given <see cref="ChatHistory"/> and <see cref="GeminiPromptExecutionSettings"/>.
    /// </summary>
    /// <param name="chatHistory">The chat history to be assigned to the GeminiRequest.</param>
    /// <param name="executionSettings">The execution settings to be applied to the GeminiRequest.</param>
    /// <returns>A new instance of <see cref="GeminiRequest"/>.</returns>
    public static GeminiRequest FromChatHistoryAndExecutionSettings(
        ChatHistory chatHistory,
        GeminiPromptExecutionSettings executionSettings)
    {
        GeminiRequest obj = CreateGeminiRequest(chatHistory);
        AddSafetySettings(executionSettings, obj);
        AddConfiguration(executionSettings, obj);
        return obj;
    }

    private static GeminiRequest CreateGeminiRequest(string prompt)
    {
        GeminiRequest obj = new()
        {
            Contents =
            [
                new()
                {
                    Parts =
                    [
                        new()
                        {
                            Text = prompt
                        }
                    ]
                }
            ]
        };
        return obj;
    }

    private static GeminiRequest CreateGeminiRequest(ChatHistory chatHistory)
    {
        GeminiRequest obj = new()
        {
            Contents = chatHistory.Select(CreateGeminiContentFromChatMessage).ToList()
        };
        return obj;
    }

    private static GeminiContent CreateGeminiContentFromChatMessage(ChatMessageContent message)
    {
        return new GeminiContent
        {
            Parts = CreateGeminiParts(message),
            Role = message.Role
        };
    }

    public void AddChatMessage(ChatMessageContent message)
    {
        Verify.NotNull(this.Contents);
        Verify.NotNull(message);

        this.Contents.Add(CreateGeminiContentFromChatMessage(message));
    }

    private static List<GeminiPart> CreateGeminiParts(ChatMessageContent content)
    {
        List<GeminiPart> parts = [];
        switch (content)
        {
            case GeminiChatMessageContent { CalledToolResult: not null } contentWithCalledTool:
                parts.Add(new GeminiPart
                {
                    FunctionResponse = new GeminiPart.FunctionResponsePart
                    {
                        FunctionName = contentWithCalledTool.CalledToolResult.FullyQualifiedName,
                        Response = new(contentWithCalledTool.CalledToolResult.FunctionResult.GetValue<object>())
                    }
                });
                break;
            case GeminiChatMessageContent { ToolCalls: not null } contentWithToolCalls:
                parts.AddRange(contentWithToolCalls.ToolCalls.Select(toolCall =>
                    new GeminiPart
                    {
                        FunctionCall = new GeminiPart.FunctionCallPart
                        {
                            FunctionName = toolCall.FullyQualifiedName,
                            Arguments = JsonSerializer.SerializeToNode(toolCall.Arguments),
                        }
                    }));
                break;
            default:
                parts.AddRange(content.Items.Select(GetGeminiPartFromKernelContent));
                break;
        }

        if (parts.Count == 0)
        {
            parts.Add(new GeminiPart { Text = content.Content ?? string.Empty });
        }

        return parts;
    }

    private static GeminiPart GetGeminiPartFromKernelContent(KernelContent item) => item switch
    {
        TextContent textContent => new GeminiPart { Text = textContent.Text },
        ImageContent imageContent => CreateGeminiPartFromImage(imageContent),
        _ => throw new NotSupportedException($"Unsupported content type. {item.GetType().Name} is not supported by Gemini.")
    };

    private static GeminiPart CreateGeminiPartFromImage(ImageContent imageContent)
    {
        // Binary data takes precedence over URI as per the ImageContent.ToString() implementation.
        if (imageContent.Data is { IsEmpty: false })
        {
            return new GeminiPart
            {
                InlineData = new GeminiPart.InlineDataPart
                {
                    MimeType = GetMimeTypeFromImageContent(imageContent),
                    InlineData = Convert.ToBase64String(imageContent.Data.Value.ToArray())
                }
            };
        }

        if (imageContent.Uri is not null)
        {
            return new GeminiPart
            {
                FileData = new GeminiPart.FileDataPart
                {
                    MimeType = GetMimeTypeFromImageContent(imageContent),
                    FileUri = imageContent.Uri ?? throw new InvalidOperationException("Image content URI is empty.")
                }
            };
        }

        throw new InvalidOperationException("Image content does not contain any data or uri.");
    }

    private static string GetMimeTypeFromImageContent(ImageContent imageContent)
    {
        return imageContent.MimeType
               ?? throw new InvalidOperationException("Image content MimeType is empty.");
    }

    private static void AddConfiguration(GeminiPromptExecutionSettings executionSettings, GeminiRequest request)
    {
        request.Configuration = new ConfigurationElement
        {
            Temperature = executionSettings.Temperature,
            TopP = executionSettings.TopP,
            TopK = executionSettings.TopK,
            MaxOutputTokens = executionSettings.MaxTokens,
            StopSequences = executionSettings.StopSequences,
            CandidateCount = executionSettings.CandidateCount
        };
    }

    private static void AddSafetySettings(GeminiPromptExecutionSettings executionSettings, GeminiRequest request)
    {
        request.SafetySettings = executionSettings.SafetySettings?.Select(s
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
