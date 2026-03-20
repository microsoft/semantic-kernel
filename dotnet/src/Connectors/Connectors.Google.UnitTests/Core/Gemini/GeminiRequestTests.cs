// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;
using TextContent = Microsoft.SemanticKernel.TextContent;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

public sealed class GeminiRequestTests
{
    [Fact]
    public void FromPromptItReturnsWithConfiguration()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9,
            AudioTimestamp = true,
            ResponseMimeType = "application/json",
            ResponseSchema = JsonElement.Parse(@"{""schema"":""schema""}")
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.Temperature, request.Configuration.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.Configuration.MaxOutputTokens);
        Assert.Equal(executionSettings.AudioTimestamp, request.Configuration.AudioTimestamp);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        Assert.Equal(executionSettings.ResponseSchema.ToString(), request.Configuration.ResponseSchema.ToString());
        Assert.Equal(executionSettings.TopP, request.Configuration.TopP);
    }

    [Fact]
    public void JsonElementResponseSchemaFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = Microsoft.Extensions.AI.AIJsonUtilities.CreateJsonSchema(typeof(int), serializerOptions: GeminiRequest.GetDefaultOptions())
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.NotNull(request.Configuration.ResponseSchema);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        var settingsSchema = Assert.IsType<JsonElement>(executionSettings.ResponseSchema);

        AssertDeepEquals(settingsSchema, request.Configuration.ResponseSchema.Value);
    }

    [Fact]
    public void KernelJsonSchemaFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = KernelJsonSchemaBuilder.Build(typeof(int))
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.NotNull(request.Configuration.ResponseSchema);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        AssertDeepEquals(((KernelJsonSchema)executionSettings.ResponseSchema).RootElement, request.Configuration.ResponseSchema.Value);
    }

    [Fact]
    public void JsonNodeResponseSchemaFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = JsonNode.Parse(Microsoft.Extensions.AI.AIJsonUtilities.CreateJsonSchema(typeof(int)).GetRawText())
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        Assert.NotNull(request.Configuration.ResponseSchema);
        Assert.Equal(JsonSerializer.SerializeToElement(executionSettings.ResponseSchema).GetRawText(), request.Configuration.ResponseSchema.Value.GetRawText());
    }

    [Fact]
    public void JsonDocumentResponseSchemaFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = JsonDocument.Parse(Microsoft.Extensions.AI.AIJsonUtilities.CreateJsonSchema(typeof(int)).GetRawText())
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        Assert.NotNull(request.Configuration.ResponseSchema);
        Assert.Equal(JsonSerializer.SerializeToElement(executionSettings.ResponseSchema).GetRawText(), request.Configuration.ResponseSchema.Value.GetRawText());
    }

    [Theory]
    [InlineData(typeof(int), "integer")]
    [InlineData(typeof(bool), "boolean")]
    [InlineData(typeof(string), "string")]
    [InlineData(typeof(double), "number")]
    [InlineData(typeof(GeminiRequest), "object")]
    [InlineData(typeof(List<int>), "array")]
    public void TypeResponseSchemaFromPromptReturnsAsExpected(Type type, string expectedSchemaType)
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = type
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        var schemaType = request.Configuration.ResponseSchema?.GetProperty("type").GetString();

        Assert.Equal(expectedSchemaType, schemaType);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
    }

    [Fact]
    public void FromPromptItReturnsWithSafetySettings()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings =
            [
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            ]
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromPromptItReturnsWithPrompt()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(prompt, request.Contents[0].Parts![0].Text);
    }

    [Fact]
    public void FromChatHistoryItReturnsWithConfiguration()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9,
            AudioTimestamp = true,
            ResponseMimeType = "application/json"
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.Temperature, request.Configuration.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.Configuration.MaxOutputTokens);
        Assert.Equal(executionSettings.AudioTimestamp, request.Configuration.AudioTimestamp);
        Assert.Equal(executionSettings.ResponseMimeType, request.Configuration.ResponseMimeType);
        Assert.Equal(executionSettings.TopP, request.Configuration.TopP);
    }

    [Fact]
    public void FromChatHistoryItReturnsWithSafetySettings()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings =
            [
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            ]
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromChatHistoryItReturnsWithChatHistory()
    {
        // Arrange
        string systemMessage = "system-message";
        var chatHistory = new ChatHistory(systemMessage);
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SystemInstruction?.Parts);
        Assert.Single(request.SystemInstruction.Parts);
        Assert.Equal(request.SystemInstruction.Parts[0].Text, systemMessage);
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[3].Content, c.Parts![0].Text));
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[1].Role, c.Role),
            c => Assert.Equal(chatHistory[2].Role, c.Role),
            c => Assert.Equal(chatHistory[3].Role, c.Role));
    }

    [Fact]
    public void FromChatHistoryMultipleSystemMessagesItReturnsWithSystemMessages()
    {
        // Arrange
        string[] systemMessages = ["system-message", "system-message2", "system-message3", "system-message4"];
        var chatHistory = new ChatHistory(systemMessages[0]);
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddSystemMessage(systemMessages[1]);
        chatHistory.AddMessage(AuthorRole.System,
            [new TextContent(systemMessages[2]), new TextContent(systemMessages[3])]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SystemInstruction?.Parts);
        Assert.All(systemMessages, msg => Assert.Contains(request.SystemInstruction.Parts, p => p.Text == msg));
    }

    [Fact]
    public void FromChatHistoryTextAsTextContentItReturnsWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new TextContent("user-message2")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<TextContent>().Single().Text, c.Parts![0].Text));
    }

    [Fact]
    public void FromChatHistoryImageAsImageContentItReturnsWithChatHistory()
    {
        // Arrange
        ReadOnlyMemory<byte> imageAsBytes = new byte[] { 0x00, 0x01, 0x02, 0x03 };
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(new Uri("https://example-image.com/")) { MimeType = "image/png" }]);
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(imageAsBytes, "image/png")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<ImageContent>().Single().Uri,
                c.Parts![0].FileData!.FileUri),
            c => Assert.True(imageAsBytes.ToArray()
                .SequenceEqual(Convert.FromBase64String(c.Parts![0].InlineData!.InlineData))));
    }

    [Fact]
    public void FromChatHistoryAudioAsAudioContentItReturnsWithChatHistory()
    {
        // Arrange
        ReadOnlyMemory<byte> audioAsBytes = new byte[] { 0x00, 0x01, 0x02, 0x03 };
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new AudioContent(new Uri("https://example-audio.com/file.wav")) { MimeType = "audio/wav" }]);
        chatHistory.AddUserMessage(contentItems:
            [new AudioContent(audioAsBytes, "audio/mp3")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<AudioContent>().Single().Uri,
                c.Parts![0].FileData!.FileUri),
            c => Assert.True(audioAsBytes.ToArray()
                .SequenceEqual(Convert.FromBase64String(c.Parts![0].InlineData!.InlineData))));
    }

    [Fact]
    public void FromChatHistoryPdfAsBinaryContentItReturnsWithChatHistory()
    {
        // Arrange
        ReadOnlyMemory<byte> pdfAsBytes = new byte[] { 0x00, 0x01, 0x02, 0x03 };
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new BinaryContent(new Uri("https://example-file.com/file.pdf")) { MimeType = "application/pdf" }]);
        chatHistory.AddUserMessage(contentItems:
            [new BinaryContent(pdfAsBytes, "application/pdf")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<BinaryContent>().Single().Uri,
                c.Parts![0].FileData!.FileUri),
            c => Assert.True(pdfAsBytes.ToArray()
                .SequenceEqual(Convert.FromBase64String(c.Parts![0].InlineData!.InlineData))));
    }

    [Fact]
    public void FromChatHistoryUnsupportedContentItThrowsNotSupportedException()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new DummyContent("unsupported-content")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        void Act() => GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Throws<NotSupportedException>(Act);
    }

    [Fact]
    public void FromChatHistoryCalledToolNotNullAddsFunctionResponse()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "");
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart { FunctionName = "function-name" });
        GeminiFunctionToolResult toolCallResult = new(toolCall, new FunctionResult(kernelFunction, expectedArgs));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Tool, string.Empty, "modelId", toolCallResult));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents,
            c => c.Role == AuthorRole.Tool);
        Assert.Single(request.Contents,
            c => c.Parts![0].FunctionResponse is not null);
        Assert.Single(request.Contents,
            c => string.Equals(c.Parts![0].FunctionResponse!.FunctionName, toolCallResult.FullyQualifiedName, StringComparison.Ordinal));
        var args = request.Contents[0].Parts![0].FunctionResponse!.Response.Arguments;
        Assert.Equal(expectedArgs.ToJsonString(), args.ToJsonString());
    }

    [Fact]
    public void FromChatHistoryToolCallsNotNullAddsFunctionCalls()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var toolCallPart = new GeminiPart.FunctionCallPart
        { FunctionName = "function-name", Arguments = expectedArgs };
        var toolCallPart2 = new GeminiPart.FunctionCallPart
        { FunctionName = "function2-name", Arguments = expectedArgs };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message", "model-id", functionsToolCalls: [toolCallPart]));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message2", "model-id2", functionsToolCalls: [toolCallPart2]));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);
        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role));
        Assert.Collection(request.Contents,
            c => Assert.NotNull(c.Parts![0].FunctionCall),
            c => Assert.NotNull(c.Parts![0].FunctionCall));
        Assert.Collection(request.Contents,
            c => Assert.Equal(c.Parts![0].FunctionCall!.FunctionName, toolCallPart.FunctionName),
            c => Assert.Equal(c.Parts![0].FunctionCall!.FunctionName, toolCallPart2.FunctionName));
        Assert.Collection(request.Contents,
            c => Assert.Equal(expectedArgs.ToJsonString(),
                c.Parts![0].FunctionCall!.Arguments!.ToJsonString()),
            c => Assert.Equal(expectedArgs.ToJsonString(),
                c.Parts![0].FunctionCall!.Arguments!.ToJsonString()));
    }

    [Fact]
    public void AddFunctionToGeminiRequest()
    {
        // Arrange
        var request = new GeminiRequest();
        var function = new GeminiFunction("function-name", "function-description", "desc", null, null);

        // Act
        request.AddFunction(function);

        // Assert
        Assert.Collection(request.Tools!.Single().Functions,
            func => Assert.Equivalent(function.ToFunctionDeclaration(), func, strict: true));
    }

    [Fact]
    public void AddMultipleFunctionsToGeminiRequest()
    {
        // Arrange
        var request = new GeminiRequest();
        var functions = new[]
        {
            new GeminiFunction("function-name", "function-description", "desc", null, null),
            new GeminiFunction("function-name2", "function-description2", "desc2", null, null)
        };

        // Act
        request.AddFunction(functions[0]);
        request.AddFunction(functions[1]);

        // Assert
        Assert.Collection(request.Tools!.Single().Functions,
            func => Assert.Equivalent(functions[0].ToFunctionDeclaration(), func, strict: true),
            func => Assert.Equivalent(functions[1].ToFunctionDeclaration(), func, strict: true));
    }

    [Fact]
    public void AddChatMessageToRequest()
    {
        // Arrange
        ChatHistory chat = [];
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chat, new GeminiPromptExecutionSettings());
        var message = new GeminiChatMessageContent(AuthorRole.User, "user-message", "model-id", calledToolResults: null);

        // Act
        request.AddChatMessage(message);

        // Assert
        Assert.Single(request.Contents,
            c => string.Equals(message.Content, c.Parts![0].Text, StringComparison.Ordinal));
        Assert.Single(request.Contents,
            c => Equals(message.Role, c.Role));
    }

    [Fact]
    public void CachedContentFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            CachedContent = "xyz/abc"
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.CachedContent, request.CachedContent);
    }

    [Fact]
    public void LabelsFromPromptReturnsAsExpected()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Labels = new Dictionary<string, string> { { "key1", "value1" }, { "key2", "value2" } }
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Labels);
        Assert.Equal(executionSettings.Labels, request.Labels);
    }

    [Fact]
    public void CachedContentFromChatHistoryReturnsAsExpected()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            CachedContent = "xyz/abc"
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Equal(executionSettings.CachedContent, request.CachedContent);
    }

    [Fact]
    public void LabelsFromChatHistoryReturnsAsExpected()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Labels = new Dictionary<string, string> { { "key1", "value1" }, { "key2", "value2" } }
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Equal(executionSettings.Labels, request.Labels);
    }

    [Fact]
    public void ResponseSchemaConvertsNullableTypesToOpenApiFormat()
    {
        // Arrange
        var prompt = "prompt-example";
        var schemaWithNullableArray = """
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": ["string", "null"],
                        "description": "user name"
                    },
                    "age": {
                        "type": ["integer", "null"],
                        "description": "user age"
                    }
                }
            }
            """;

        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = JsonElement.Parse(schemaWithNullableArray)
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration?.ResponseSchema);
        var properties = request.Configuration.ResponseSchema.Value.GetProperty("properties");

        var nameProperty = properties.GetProperty("name");
        Assert.Equal("string", nameProperty.GetProperty("type").GetString());
        Assert.True(nameProperty.GetProperty("nullable").GetBoolean());

        var ageProperty = properties.GetProperty("age");
        Assert.Equal("integer", ageProperty.GetProperty("type").GetString());
        Assert.True(ageProperty.GetProperty("nullable").GetBoolean());
    }

    [Fact]
    public void ResponseSchemaAddsTypeToEnumProperties()
    {
        // Arrange
        var prompt = "prompt-example";
        var schemaWithEnum = """
            {
                "properties" : {
                    "Movies": {
                        "type" : "array",
                        "items" : {
                            "type" : "object",
                            "properties" : {
                                "status": {
                                    "enum": ["active", "inactive", null],
                                    "description": "user status"
                                },
                                "role": {
                                    "enum": ["admin", "user"],
                                    "description": "user role"
                                }
                            }
                        }
                    }
                }
            }
            """;

        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseMimeType = "application/json",
            ResponseSchema = JsonElement.Parse(schemaWithEnum)
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration?.ResponseSchema);
        var properties = request.Configuration.ResponseSchema.Value
            .GetProperty("properties")
            .GetProperty("Movies")
            .GetProperty("items")
            .GetProperty("properties");

        var statusProperty = properties.GetProperty("status");
        Assert.Equal("string", statusProperty.GetProperty("type").GetString());
        Assert.Equal(3, statusProperty.GetProperty("enum").GetArrayLength());

        var roleProperty = properties.GetProperty("role");
        Assert.Equal("string", roleProperty.GetProperty("type").GetString());
        Assert.Equal(2, roleProperty.GetProperty("enum").GetArrayLength());
    }

    [Fact]
    public void FromPromptAndExecutionSettingsWithThinkingConfigReturnsInGenerationConfig()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ModelId = "gemini-2.5-flash-preview-04-17",
            ThinkingConfig = new GeminiThinkingConfig { ThinkingBudget = 1024 }
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(executionSettings.ThinkingConfig.ThinkingBudget, request.Configuration?.ThinkingConfig?.ThinkingBudget);
    }

    [Fact]
    public void FromPromptAndExecutionSettingsWithThinkingLevelReturnsInGenerationConfig()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ModelId = "gemini-3.0-flash",
            ThinkingConfig = new GeminiThinkingConfig { ThinkingLevel = "high" }
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(executionSettings.ThinkingConfig.ThinkingLevel, request.Configuration?.ThinkingConfig?.ThinkingLevel);
    }

    [Fact]
    public void FromChatHistorySingleAssistantMessageSetsRoleToNull()
    {
        // Arrange - Single assistant message (issue #13262 scenario)
        ChatHistory chatHistory = [];
        chatHistory.AddAssistantMessage("assistant-message");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert - Role should be null to fix issue #13262 (Gemini requires single-turn requests to end with user role or no role)
        Assert.Single(request.Contents);
        Assert.Null(request.Contents[0].Role);
        Assert.Equal("assistant-message", request.Contents[0].Parts![0].Text);
    }

    [Fact]
    public void FromChatHistoryMultiTurnConversationPreservesAllRoles()
    {
        // Arrange - Multi-turn conversation should not be affected by the fix
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message-1");
        chatHistory.AddAssistantMessage("assistant-message-1");
        chatHistory.AddUserMessage("user-message-2");
        chatHistory.AddAssistantMessage("assistant-message-2");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert - All roles should be preserved in multi-turn conversations
        Assert.Equal(4, request.Contents.Count);
        Assert.Equal(AuthorRole.User, request.Contents[0].Role);
        Assert.Equal(AuthorRole.Assistant, request.Contents[1].Role);
        Assert.Equal(AuthorRole.User, request.Contents[2].Role);
        Assert.Equal(AuthorRole.Assistant, request.Contents[3].Role);
        Assert.Equal("user-message-1", request.Contents[0].Parts![0].Text);
        Assert.Equal("assistant-message-1", request.Contents[1].Parts![0].Text);
        Assert.Equal("user-message-2", request.Contents[2].Parts![0].Text);
        Assert.Equal("assistant-message-2", request.Contents[3].Parts![0].Text);
    }

    [Fact]
    public void FromChatHistoryToolCallsWithThoughtSignatureIncludesSignatureInRequest()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var inputPart = new GeminiPart
        {
            FunctionCall = new GeminiPart.FunctionCallPart
            {
                FunctionName = "function-name",
                Arguments = new JsonObject { ["key"] = "value" }
            },
            ThoughtSignature = "thought-signature-abc123"
        };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message", "model-id", [inputPart]));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents);
        var requestParts = request.Contents[0].Parts;
        Assert.NotNull(requestParts);
        var requestPart = Assert.Single(requestParts);
        Assert.NotNull(requestPart.FunctionCall);
        Assert.Equal("thought-signature-abc123", requestPart.ThoughtSignature);
    }

    [Fact]
    public void FromChatHistoryToolCallsWithoutThoughtSignatureDoesNotIncludeSignature()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var functionCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = "function-name",
            Arguments = new JsonObject { ["key"] = "value" }
        };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message", "model-id", functionsToolCalls: [functionCallPart]));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents);
        var requestParts = request.Contents[0].Parts;
        Assert.NotNull(requestParts);
        var requestPart = Assert.Single(requestParts);
        Assert.Null(requestPart.ThoughtSignature);
    }

    [Fact]
    public void FromChatHistoryParallelToolCallsOnlyFirstHasThoughtSignature()
    {
        // Arrange - Parallel function calls: only first has ThoughtSignature per Google docs
        ChatHistory chatHistory = [];
        var geminiParts = new[]
        {
            new GeminiPart
            {
                FunctionCall = new GeminiPart.FunctionCallPart { FunctionName = "function1" },
                ThoughtSignature = "signature-for-first-only"
            },
            new GeminiPart
            {
                FunctionCall = new GeminiPart.FunctionCallPart { FunctionName = "function2" },
                ThoughtSignature = null
            },
            new GeminiPart
            {
                FunctionCall = new GeminiPart.FunctionCallPart { FunctionName = "function3" },
                ThoughtSignature = null
            }
        };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, null, "model-id", geminiParts));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents);
        var parts = request.Contents[0].Parts;
        Assert.NotNull(parts);
        Assert.Equal(3, parts.Count);
        Assert.Equal("signature-for-first-only", parts[0].ThoughtSignature);
        Assert.Null(parts[1].ThoughtSignature);
        Assert.Null(parts[2].ThoughtSignature);
    }

    [Fact]
    public void FromChatHistoryTextResponseWithThoughtSignatureIncludesSignatureInRequest()
    {
        // Arrange - Text response with ThoughtSignature in Metadata
        ChatHistory chatHistory = [];
        var metadata = new GeminiMetadata { ThoughtSignature = "text-response-signature" };
        chatHistory.Add(new GeminiChatMessageContent(
            AuthorRole.Assistant,
            "This is a text response",
            "model-id",
            calledToolResults: null,
            metadata));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents);
        var parts = request.Contents[0].Parts;
        Assert.NotNull(parts);
        var part = Assert.Single(parts);
        Assert.Equal("This is a text response", part.Text);
        Assert.Equal("text-response-signature", part.ThoughtSignature);
    }

    [Fact]
    public void FromChatHistoryTextResponseWithoutThoughtSignatureDoesNotIncludeSignature()
    {
        // Arrange - Text response without ThoughtSignature (thinking disabled)
        ChatHistory chatHistory = [];
        chatHistory.AddAssistantMessage("This is a text response");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents);
        var parts = request.Contents[0].Parts;
        Assert.NotNull(parts);
        var part = Assert.Single(parts);
        Assert.Null(part.ThoughtSignature);
    }

    [Fact]
    public void FromChatHistoryMultiTurnWithThoughtSignaturesPreservesAllSignatures()
    {
        // Arrange - Multi-turn conversation with different ThoughtSignatures
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("Question 1");

        var metadata1 = new GeminiMetadata { ThoughtSignature = "signature-turn-1" };
        chatHistory.Add(new GeminiChatMessageContent(
            AuthorRole.Assistant,
            "Answer 1",
            "model-id",
            calledToolResults: null,
            metadata1));

        chatHistory.AddUserMessage("Question 2");

        var metadata2 = new GeminiMetadata { ThoughtSignature = "signature-turn-2" };
        chatHistory.Add(new GeminiChatMessageContent(
            AuthorRole.Assistant,
            "Answer 2",
            "model-id",
            calledToolResults: null,
            metadata2));

        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Equal(4, request.Contents.Count);
        Assert.Null(request.Contents[0].Parts![0].ThoughtSignature); // User message
        Assert.Equal("signature-turn-1", request.Contents[1].Parts![0].ThoughtSignature); // Assistant 1
        Assert.Null(request.Contents[2].Parts![0].ThoughtSignature); // User message
        Assert.Equal("signature-turn-2", request.Contents[3].Parts![0].ThoughtSignature); // Assistant 2
    }

    [Fact]
    public void FromChatHistoryThoughtSignatureFromDictionaryMetadataFallback()
    {
        // Arrange - Simulate deserialized chat history where Metadata is a dictionary
        ChatHistory chatHistory = [];
        var metadata = new Dictionary<string, object?> { ["ThoughtSignature"] = "fallback-signature" };
        chatHistory.Add(new ChatMessageContent(AuthorRole.Assistant, "Text response", "model-id", metadata));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert - Should NOT include signature because it's not a GeminiChatMessageContent
        // The fallback only works for GeminiChatMessageContent with dictionary metadata
        Assert.Single(request.Contents);
        Assert.Null(request.Contents[0].Parts![0].ThoughtSignature);
    }

    private sealed class DummyContent(object? innerContent, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null) :
        KernelContent(innerContent, modelId, metadata);

    private static bool DeepEquals(JsonElement element1, JsonElement element2)
    {
        return JsonElement.DeepEquals(element1, element2);
    }

    private static void AssertDeepEquals(JsonElement element1, JsonElement element2)
    {
#pragma warning disable SA1118 // Parameter should not span multiple lines
        Assert.True(DeepEquals(element1, element2), $"""
                                                     Elements are not equal.
                                                     Expected:
                                                     {element1}
                                                     Actual:
                                                     {element2}
                                                     """);
#pragma warning restore SA1118 // Parameter should not span multiple lines
    }
}
