// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Client;

/// <summary>
/// Unit tests for <see cref="MistralClient"/>.
/// </summary>
public sealed class MistralClientTests : IDisposable
{
    private AssertingDelegatingHandler? _delegatingHandler;
    private HttpClient? _httpClient;

    [Fact]
    public void ValidateRequiredArguments()
    {
        // Arrange
        // Act
        // Assert
        Assert.Throws<ArgumentException>(() => new MistralClient(string.Empty, new HttpClient(), "key"));
        Assert.Throws<ArgumentException>(() => new MistralClient("model", new HttpClient(), string.Empty));
#pragma warning disable CS8625 // Cannot convert null literal to non-nullable reference type.
        Assert.Throws<ArgumentNullException>(() => new MistralClient(null, new HttpClient(), "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", null, "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", new HttpClient(), null));
#pragma warning restore CS8625 // Cannot convert null literal to non-nullable reference type.
    }

    [Fact]
    public async Task ValidateChatMessageRequestAsync()
    {
        // Arrange
        var response = this.GetTestData("chat_completions_response.json");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", response);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-small-latest", this._httpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { MaxTokens = 1024, Temperature = 0.9 };
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings);

        // Assert
        var request = this._delegatingHandler.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("mistral-small-latest", chatRequest.Model);
        Assert.Equal(1024, chatRequest.MaxTokens);
        Assert.Equal(0.9, chatRequest.Temperature);
        Assert.Single(chatRequest.Messages);
        Assert.Equal("user", chatRequest.Messages[0].Role);
        Assert.Equal("What is the best French cheese?", chatRequest.Messages[0].Content);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestData("chat_completions_response.json");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this._httpClient, "key");

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
        Assert.Equal("mistral-tiny", response[0].ModelId);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
        Assert.NotNull(response[0].Metadata);
        Assert.Equal(7, response[0].Metadata?.Count);
    }

    [Fact]
    public async Task ValidateGenerateEmbeddingsAsync()
    {
        // Arrange
        var content = this.GetTestData("embeddings_response.json");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/embeddings", content);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this._httpClient, "key");

        // Act
        List<string> data = new() { "Hello", "world" };
        var response = await client.GenerateEmbeddingsAsync(data, default);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Length);
        Assert.Equal(1024, response[1].Length);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsStream("chat_completions_streaming_response.txt");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this._httpClient, "key");

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = client.GetStreamingChatMessageContentsAsync(chatHistory, default);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        };

        // Assert
        Assert.NotNull(response);
        Assert.Equal(124, chunks.Count);
        foreach (var chunk in chunks)
        {
            Assert.NotNull(chunk);
            Assert.Equal("mistral-tiny", chunk.ModelId);
            Assert.NotNull(chunk.Content);
            Assert.NotNull(chunk.Role);
            Assert.NotNull(chunk.Metadata);
        }
    }

    [Fact]
    public async Task ValidateChatHistoryAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsStream("chat_completions_streaming_response.txt");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this._httpClient, "key");

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Assistant, "What is the best French cheese?")
        };

        // Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await client.GetChatMessageContentsAsync(chatHistory, default));
    }

    [Fact]
    public async Task ValidateChatMessageRequestWithToolsAsync()
    {
        // Arrange
        var response = this.GetTestData("function_call_response.json");
        this._delegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", response);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-small-latest", this._httpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.EnableKernelFunctions };

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        var request = this._delegatingHandler.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("auto", chatRequest.ToolChoice);
        Assert.NotNull(chatRequest.Tools);
        Assert.Single(chatRequest.Tools);
        Assert.NotNull(chatRequest.Tools[0].Function.Parameters);
        Assert.Equal(["location", "units"], chatRequest.Tools[0].Function.Parameters?.Required);
        Assert.Equal("string", chatRequest.Tools[0].Function.Parameters?.Properties["location"].RootElement.GetProperty("type").GetString());
        Assert.Equal(2, chatRequest.Tools[0].Function.Parameters?.Properties["units"].RootElement.GetProperty("enum").GetArrayLength());
    }

    public void Dispose()
    {
        this._delegatingHandler?.Dispose();
        this._httpClient?.Dispose();
    }

    #region private

    private string GetTestData(string fileName)
    {
        return File.ReadAllText($"./TestData/{fileName}");
    }

    private MemoryStream GetTestResponseAsStream(string fileName)
    {
        var bytes = File.ReadAllBytes($"./TestData/{fileName}");
        return new MemoryStream(bytes);
    }

    private static HttpRequestHeaders GetDefaultRequestHeaders(string key, bool stream)
    {
#pragma warning disable CA2000 // Dispose objects before losing scope
        var requestHeaders = new HttpRequestMessage().Headers;
#pragma warning restore CA2000 // Dispose objects before losing scope
        requestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        requestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(MistralClient)));
        requestHeaders.Add("Accept", stream ? "text/event-stream" : "application/json");
        requestHeaders.Add("Authorization", $"Bearer {key}");

        return requestHeaders;
    }

    #endregion

    #region internal classes

    internal sealed class AssertingDelegatingHandler : DelegatingHandler
    {
        public Uri RequestUri { get; init; }
        public HttpMethod Method { get; init; } = HttpMethod.Post;
        public HttpRequestHeaders RequestHeaders { get; init; } = GetDefaultRequestHeaders("key", false);
        public HttpResponseMessage ResponseMessage { get; init; } = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        public string? RequestContent { get; private set; } = null;

        internal AssertingDelegatingHandler(string requestUri, string responseContent)
        {
            this.RequestUri = new Uri(requestUri);
            this.RequestHeaders = GetDefaultRequestHeaders("key", false);
            this.ResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(responseContent, System.Text.Encoding.UTF8, "application/json")
            };
        }

        internal AssertingDelegatingHandler(string requestUri, Stream content)
        {
            this.RequestUri = new Uri(requestUri);
            this.RequestHeaders = GetDefaultRequestHeaders("key", true);
            this.ResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StreamContent(content)
            };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Assert.Equal(this.RequestUri, request.RequestUri);
            Assert.Equal(this.Method, request.Method);
            Assert.Equal(this.RequestHeaders, request.Headers);

            this.RequestContent = await request.Content!.ReadAsStringAsync(cancellationToken);

            return await Task.FromResult(this.ResponseMessage);
        }
    }

    internal sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location,
            [Description("The temperature units one of celsius or fahrenheit")] TemperatureUnit units
            ) => $"{{\"location\": \"{location}\", \"unit\": \"{units}\"}}";
    }

    internal enum TemperatureUnit { Celsius, Fahrenheit }

    #endregion
}
