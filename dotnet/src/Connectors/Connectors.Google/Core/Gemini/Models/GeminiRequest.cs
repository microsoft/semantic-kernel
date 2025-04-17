// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class GeminiRequest
{
    private static JsonSerializerOptions? s_options;
    private static readonly AIJsonSchemaCreateOptions s_schemaOptions = new()
    {
        IncludeSchemaKeyword = false,
        IncludeTypeInEnumSchemas = true,
        RequireAllProperties = false,
        DisallowAdditionalProperties = false,
    };

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

    [JsonPropertyName("systemInstruction")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiContent? SystemInstruction { get; set; }

    [JsonPropertyName("cachedContent")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? CachedContent { get; set; }

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
        AddAdditionalBodyFields(executionSettings, obj);
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
        AddAdditionalBodyFields(executionSettings, obj);
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
            Contents = chatHistory
                .Where(message => message.Role != AuthorRole.System)
                .Select(CreateGeminiContentFromChatMessage).ToList(),
            SystemInstruction = CreateSystemMessages(chatHistory)
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

    private static GeminiContent? CreateSystemMessages(ChatHistory chatHistory)
    {
        var contents = chatHistory.Where(message => message.Role == AuthorRole.System).ToList();
        if (contents.Count == 0)
        {
            return null;
        }

        return new GeminiContent
        {
            Parts = CreateGeminiParts(contents)
        };
    }

    public void AddChatMessage(ChatMessageContent message)
    {
        Verify.NotNull(this.Contents);
        Verify.NotNull(message);

        this.Contents.Add(CreateGeminiContentFromChatMessage(message));
    }

    private static List<GeminiPart> CreateGeminiParts(IEnumerable<ChatMessageContent> contents)
    {
        List<GeminiPart>? parts = null;
        foreach (var content in contents)
        {
            if (parts == null)
            {
                parts = CreateGeminiParts(content);
            }
            else
            {
                parts.AddRange(CreateGeminiParts(content));
            }
        }

        return parts!;
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
        AudioContent audioContent => CreateGeminiPartFromAudio(audioContent),
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

    private static GeminiPart CreateGeminiPartFromAudio(AudioContent audioContent)
    {
        // Binary data takes precedence over URI.
        if (audioContent.Data is { IsEmpty: false })
        {
            return new GeminiPart
            {
                InlineData = new GeminiPart.InlineDataPart
                {
                    MimeType = GetMimeTypeFromAudioContent(audioContent),
                    InlineData = Convert.ToBase64String(audioContent.Data.Value.ToArray())
                }
            };
        }

        if (audioContent.Uri is not null)
        {
            return new GeminiPart
            {
                FileData = new GeminiPart.FileDataPart
                {
                    MimeType = GetMimeTypeFromAudioContent(audioContent),
                    FileUri = audioContent.Uri ?? throw new InvalidOperationException("Audio content URI is empty.")
                }
            };
        }

        throw new InvalidOperationException("Audio content does not contain any data or uri.");
    }

    private static string GetMimeTypeFromAudioContent(AudioContent audioContent)
    {
        return audioContent.MimeType
               ?? throw new InvalidOperationException("Audio content MimeType is empty.");
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
            CandidateCount = executionSettings.CandidateCount,
            AudioTimestamp = executionSettings.AudioTimestamp,
            ResponseMimeType = executionSettings.ResponseMimeType,
            ResponseSchema = GetResponseSchemaConfig(executionSettings.ResponseSchema)
        };
    }

    internal static JsonElement? GetResponseSchemaConfig(object? responseSchemaSettings)
    {
        if (responseSchemaSettings is null)
        {
            return null;
        }

        var jsonElement = responseSchemaSettings switch
        {
            JsonElement element => element,
            Type type => CreateSchema(type, GetDefaultOptions()),
            KernelJsonSchema kernelJsonSchema => kernelJsonSchema.RootElement,
            JsonNode jsonNode => JsonSerializer.SerializeToElement(jsonNode, GetDefaultOptions()),
            JsonDocument jsonDocument => JsonSerializer.SerializeToElement(jsonDocument, GetDefaultOptions()),
            _ => CreateSchema(responseSchemaSettings.GetType(), GetDefaultOptions())
        };

        jsonElement = TransformToOpenApi3Schema(jsonElement);
        return jsonElement;
    }

    /// <summary>
    /// Adjusts the schema to conform to OpenAPI 3.0 nullable format by converting properties with type arrays
    /// containing "null" (e.g., ["string", "null"]) to use the "nullable" keyword instead (e.g., { "type": "string", "nullable": true }).
    /// </summary>
    /// <param name="jsonElement">The JSON schema to be transformed.</param>
    /// <returns>A new JsonElement with the adjusted schema format.</returns>
    /// <remarks>
    /// This method recursively processes all nested objects in the schema. For each property that has a type array
    /// containing "null", it:
    /// - Extracts the main type (non-null value)
    /// - Replaces the type array with a single type value
    /// - Adds "nullable": true as a property
    /// </remarks>
    private static JsonElement TransformToOpenApi3Schema(JsonElement jsonElement)
    {
        JsonNode? node = JsonNode.Parse(jsonElement.GetRawText());
        if (node is JsonObject rootObject)
        {
            TransformOpenApi3Object(rootObject);
        }

        return JsonSerializer.SerializeToElement(node, GetDefaultOptions());

        static void TransformOpenApi3Object(JsonObject obj)
        {
            if (obj.TryGetPropertyValue("properties", out JsonNode? propsNode) && propsNode is JsonObject properties)
            {
                foreach (var property in properties)
                {
                    if (property.Value is JsonObject propertyObj)
                    {
                        // Handle enum properties - add "type": "string" if missing
                        if (propertyObj.TryGetPropertyValue("enum", out JsonNode? enumNode) && !propertyObj.ContainsKey("type"))
                        {
                            propertyObj["type"] = JsonValue.Create("string");
                        }
                        else if (propertyObj.TryGetPropertyValue("type", out JsonNode? typeNode))
                        {
                            if (typeNode is JsonArray typeArray)
                            {
                                var types = typeArray.Select(t => t?.GetValue<string>()).Where(t => t != null).ToList();
                                if (types.Contains("null"))
                                {
                                    var mainType = types.First(t => t != "null");
                                    propertyObj["type"] = JsonValue.Create(mainType);
                                    propertyObj["nullable"] = JsonValue.Create(true);
                                }
                            }
                            else if (typeNode is JsonValue typeValue && typeValue.GetValue<string>() == "array")
                            {
                                if (propertyObj.TryGetPropertyValue("items", out JsonNode? itemsNode) && itemsNode is JsonObject itemsObj)
                                {
                                    TransformOpenApi3Object(itemsObj);
                                }
                            }
                        }

                        // Recursively process nested objects
                        TransformOpenApi3Object(propertyObj);
                    }
                }
            }
        }
    }

    private static JsonElement CreateSchema(
        Type type,
        JsonSerializerOptions options,
        string? description = null,
        AIJsonSchemaCreateOptions? configuration = null)
    {
        configuration ??= s_schemaOptions;
        return AIJsonUtilities.CreateJsonSchema(type, description, serializerOptions: options, inferenceOptions: configuration);
    }

    internal static JsonSerializerOptions GetDefaultOptions()
    {
        if (s_options is null)
        {
            JsonSerializerOptions options = new()
            {
                TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
                Converters = { new JsonStringEnumConverter() },
            };
            options.MakeReadOnly();
            s_options = options;
        }

        return s_options;
    }

    private static void AddSafetySettings(GeminiPromptExecutionSettings executionSettings, GeminiRequest request)
    {
        request.SafetySettings = executionSettings.SafetySettings?.Select(s
            => new GeminiSafetySetting(s.Category, s.Threshold)).ToList();
    }

    private static void AddAdditionalBodyFields(GeminiPromptExecutionSettings executionSettings, GeminiRequest request)
    {
        request.CachedContent = executionSettings.CachedContent;
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

        [JsonPropertyName("audioTimestamp")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? AudioTimestamp { get; set; }

        [JsonPropertyName("responseMimeType")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? ResponseMimeType { get; set; }

        [JsonPropertyName("responseSchema")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public JsonElement? ResponseSchema { get; set; }
    }
}
