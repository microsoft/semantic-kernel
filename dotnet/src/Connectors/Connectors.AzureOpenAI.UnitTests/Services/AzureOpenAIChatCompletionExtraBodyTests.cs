// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests verifying that <see cref="OpenAIPromptExecutionSettings.ExtraBody"/> is honored by
/// the <see cref="AzureOpenAIChatCompletionService"/> classic path.
/// </summary>
public sealed class AzureOpenAIChatCompletionExtraBodyTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly ChatHistory _chatHistory = [new ChatMessageContent(AuthorRole.User, "test")];

    public AzureOpenAIChatCompletionExtraBodyTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
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
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(AzureOpenAITestHelper.GetTestResponse("chat_completion_test_response.json")),
        });
        var settings = new AzureOpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["enable_thinking"] = false,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContents[0]!);
        Assert.True(body.TryGetProperty("enable_thinking", out var value));
        Assert.False(value.GetBoolean());
    }

    [Fact]
    public async Task ExtraBodyOverridesFirstClassPropertyAsync()
    {
        // Arrange - last-write-wins.
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(AzureOpenAITestHelper.GetTestResponse("chat_completion_test_response.json")),
        });
        var settings = new AzureOpenAIPromptExecutionSettings
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
        var body = ParseRequestBody(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal(0.0, body.GetProperty("temperature").GetDouble());
    }

    [Fact]
    public async Task ExtraBodyJsonPathPrefixDoesDeepPatchAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(AzureOpenAITestHelper.GetTestResponse("chat_completion_test_response.json")),
        });
        var settings = new AzureOpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                ["$.thinking.enabled"] = false,
            },
        };

        // Act
        await service.GetChatMessageContentsAsync(this._chatHistory, settings);

        // Assert
        var body = ParseRequestBody(this._messageHandlerStub.RequestContents[0]!);
        Assert.False(body.GetProperty("thinking").GetProperty("enabled").GetBoolean());
    }

    private static JsonElement ParseRequestBody(byte[] requestContent)
    {
        var json = Encoding.UTF8.GetString(requestContent);
        return JsonDocument.Parse(json).RootElement;
    }
}
