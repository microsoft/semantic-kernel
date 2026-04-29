// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for the <see cref="OpenAIPromptExecutionSettings.ExtraBody"/> property and its application to
/// outgoing chat completion requests.
/// </summary>
public sealed class OpenAIChatCompletionExtraBodyTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly ChatHistory _chatHistory = [new ChatMessageContent(AuthorRole.User, "test")];

    public OpenAIChatCompletionExtraBodyTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(ChatCompletionResponse),
            },
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    [Fact]
    public async Task ExtraBodyFlatKeyAppearsAtTopLevelAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["enable_thinking"] = false,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.True(body.TryGetProperty("enable_thinking", out var value));
        Assert.False(value.GetBoolean());
    }

    [Fact]
    public async Task ExtraBodyStreamingFlatKeyAppearsAtTopLevelAsync()
    {
        // Arrange
        var streamBytes = Encoding.UTF8.GetBytes(ChatCompletionStreamingResponse);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new System.IO.MemoryStream(streamBytes)),
        };
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["enable_thinking"] = false,
            },
        };

        // Act
        await foreach (var _ in service.GetStreamingChatMessageContentsAsync(this._chatHistory, settings))
        {
        }

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.True(body.TryGetProperty("enable_thinking", out var value));
        Assert.False(value.GetBoolean());
    }

    [Fact]
    public async Task ExtraBodyOverridesFirstClassPropertyAsync()
    {
        // Arrange - last-write-wins; ExtraBody value applied via JsonPatch overrides the strongly-typed property.
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            ExtraBody = new Dictionary<string, object?>
            {
                ["temperature"] = 0.0,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.Equal(0.0, body.GetProperty("temperature").GetDouble());
    }

    [Fact]
    public async Task ExtraBodyNestedDictionaryEmitsNestedJsonObjectAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["thinking"] = new Dictionary<string, object?> { ["enabled"] = false, ["budget"] = 100 },
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        var thinking = body.GetProperty("thinking");
        Assert.False(thinking.GetProperty("enabled").GetBoolean());
        Assert.Equal(100, thinking.GetProperty("budget").GetInt32());
    }

    [Fact]
    public async Task ExtraBodyJsonPathPrefixDoesDeepPatchAsync()
    {
        // Arrange - $.-prefixed key is interpreted as a JSONPath patch and creates the nested structure.
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["$.thinking.enabled"] = false,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.False(body.GetProperty("thinking").GetProperty("enabled").GetBoolean());
    }

    [Fact]
    public async Task ExtraBodyLiteralDottedKeyEmitsLiteralFieldAsync()
    {
        // Arrange - keys without $. prefix are literal, even when they contain dots.
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["weird.key"] = "literal-value",
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.True(body.TryGetProperty("weird.key", out var value));
        Assert.Equal("literal-value", value.GetString());
    }

    [Fact]
    public async Task ExtraBodyNullValueEmitsJsonNullAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["nullable_field"] = null,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContent!);
        Assert.True(body.TryGetProperty("nullable_field", out var value));
        Assert.Equal(JsonValueKind.Null, value.ValueKind);
    }

    [Fact]
    public void FromExecutionSettingsRoundTripPreservesExtraBody()
    {
        // Arrange - deserializing through the base type (e.g. via PromptTemplateConfig) should preserve extra_body.
        var jsonSettings = new PromptExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                ["temperature"] = 0.5,
                ["extra_body"] = new Dictionary<string, object?> { ["enable_thinking"] = false },
            },
        };

        // Act
        var settings = OpenAIPromptExecutionSettings.FromExecutionSettings(jsonSettings);

        // Assert
        Assert.NotNull(settings.ExtraBody);
        Assert.True(settings.ExtraBody.ContainsKey("enable_thinking"));
    }

    [Fact]
    public void CloneCopiesExtraBodyShallowly()
    {
        // Arrange
        var original = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?> { ["a"] = 1 },
        };

        // Act
        var clone = (OpenAIPromptExecutionSettings)original.Clone();
        clone.ExtraBody!["b"] = 2;

        // Assert - top-level shallow copy: adding to clone does not affect original.
        Assert.False(original.ExtraBody!.ContainsKey("b"));
        Assert.True(clone.ExtraBody.ContainsKey("a"));
        Assert.True(clone.ExtraBody.ContainsKey("b"));
    }

    [Fact]
    public void FreezeMakesExtraBodyReadOnly()
    {
        // Arrange
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?> { ["a"] = 1 },
        };

        // Act
        settings.Freeze();

        // Assert
        Assert.Throws<NotSupportedException>(() => settings.ExtraBody!["b"] = 2);
    }

    [Fact]
    public void ToChatOptionsSetsRawRepresentationFactoryAndCleansAdditionalProperties()
    {
        // Arrange - exercises the IChatClient path: PrepareChatOptionsForRequest must
        // wire ChatOptions.RawRepresentationFactory and remove the redundant extra_body entry from AdditionalProperties.
        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["enable_thinking"] = false,
                ["$.thinking.enabled"] = false,
            },
        };

        // Act
        var chatOptions = settings.ToChatOptions(kernel: null);

        // Assert
        Assert.NotNull(chatOptions);
        Assert.NotNull(chatOptions!.RawRepresentationFactory);
        Assert.False(chatOptions.AdditionalProperties?.ContainsKey("extra_body") ?? false);

        // Verify the factory produces a ChatCompletionOptions that serializes the patched fields.
        var rawObj = chatOptions.RawRepresentationFactory.Invoke(null!);
        var raw = Assert.IsType<global::OpenAI.Chat.ChatCompletionOptions>(rawObj);
        var serialized = global::System.ClientModel.Primitives.ModelReaderWriter.Write(raw).ToString();
        var json = JsonDocument.Parse(serialized).RootElement;
        Assert.False(json.GetProperty("enable_thinking").GetBoolean());
        Assert.False(json.GetProperty("thinking").GetProperty("enabled").GetBoolean());
    }

    private static JsonElement ParseRequestBody(byte[] requestContent)
    {
        var json = Encoding.UTF8.GetString(requestContent);
        return JsonDocument.Parse(json).RootElement;
    }

    private const string ChatCompletionResponse = """
        {
          "id": "chatcmpl-123",
          "object": "chat.completion",
          "created": 1677652288,
          "model": "gpt-4o",
          "choices": [{
            "index": 0,
            "message": { "role": "assistant", "content": "Hello!" },
            "finish_reason": "stop"
          }],
          "usage": { "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2 }
        }
        """;

    private const string ChatCompletionStreamingResponse =
        "data: {\"id\":\"x\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"gpt-4o\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"Hi\"},\"finish_reason\":null}]}\n\n" +
        "data: {\"id\":\"x\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"gpt-4o\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\n" +
        "data: [DONE]\n\n";
}
