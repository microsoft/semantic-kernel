// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Anthropic;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.Anthropic.ChatCompletion;

public sealed class AnthropicChatCompletionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly AnthropicRequestSettings _requestSettings;
    private readonly ITestOutputHelper _testOutputHelper;

    private static readonly string s_chatCompletionResponse = @"
{
    ""completion"": ""Hello, John Doe. Today is Friday, February 7, 2020."",
    ""stop_reason"": ""stop_sequence"",
    ""model"": ""claude-2""
}".Trim();

    public AnthropicChatCompletionTests(ITestOutputHelper testOutputHelper)
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._requestSettings = new();
        this._testOutputHelper = testOutputHelper;
    }

    [Fact]
    public async Task ItCorrectlyFormsRequestFromChatHistoryAsync()
    {
        // Arrange
        using var chatCompletion = new AnthropicChatCompletion(modelId: "claude-2", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(s_chatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        await chatCompletion.GetChatCompletionsAsync(chatHistory, this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        this._testOutputHelper.WriteLine(actualRequestContent);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal("claude-2", optionsJson.GetProperty("model").GetString());
        Assert.Equal("\n\nHuman: Hello\n\n\nAssistant: ", optionsJson.GetProperty("prompt").GetString());
    }

    [Fact]
    public async Task ItCorrectlyFormsRequestFromTextPromptAsync()
    {
        // Arrange
        using var chatCompletion = new AnthropicChatCompletion(modelId: "claude-2", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(s_chatCompletionResponse) };

        // Act
        await chatCompletion.GetCompletionsAsync("Hello", this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        this._testOutputHelper.WriteLine(actualRequestContent);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal("claude-2", optionsJson.GetProperty("model").GetString());
        Assert.Equal("\n\nHuman: Hello\n\n\nAssistant: ", optionsJson.GetProperty("prompt").GetString());
    }

    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }
}
