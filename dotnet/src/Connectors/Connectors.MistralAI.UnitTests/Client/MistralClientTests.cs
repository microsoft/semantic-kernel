// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
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
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponse("chat_completion_response.json");
        this._delegatingHandler = new AssertingDelegatingHandler(content);
        this._httpClient = new HttpClient(this._delegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this._httpClient, "key");

        // Act
        var chatHistory = new ChatHistory();
        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the best French cheese?"));
        var response = await client.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
        Assert.Equal("mistral-tiny", response[0].ModelId);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
        Assert.NotNull(response[0].Metadata);
        Assert.Equal(7, response[0].Metadata?.Count);
    }

    public void Dispose()
    {
        this._delegatingHandler?.Dispose();
        this._httpClient?.Dispose();
    }

    private string GetTestResponse(string fileName)
    {
        return File.ReadAllText($"./TestData/{fileName}");
    }

    internal sealed class AssertingDelegatingHandler : DelegatingHandler
    {
        public Uri RequestUri { get; init; } = new Uri("https://api.mistral.ai/v1");
        public HttpMethod Method { get; init; } = HttpMethod.Post;
        public HttpRequestHeaders RequestHeaders { get; init; } = GetDefaultRequestHeaders("key", false);
        public HttpResponseMessage ResponseMessage { get; init; } = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        internal AssertingDelegatingHandler(string content)
        {
            this.ResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(content, System.Text.Encoding.UTF8, "application/json")
            };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Assert.Equal(this.RequestUri, request.RequestUri);
            Assert.Equal(this.Method, request.Method);
            Assert.Equal(this.RequestHeaders, request.Headers);

            return await Task.FromResult(this.ResponseMessage);
        }

        private static HttpRequestHeaders GetDefaultRequestHeaders(string key, bool stream)
        {
            var requestHeaders = new HttpRequestMessage().Headers;
            requestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
            requestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(MistralClient)));
            requestHeaders.Add("Accept", stream ? "text/event-stream" : "application/json");
            requestHeaders.Add("Authorization", $"Bearer {key}");

            return requestHeaders;
        }
    }
}
