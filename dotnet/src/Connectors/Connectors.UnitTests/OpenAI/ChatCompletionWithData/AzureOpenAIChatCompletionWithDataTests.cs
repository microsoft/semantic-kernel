// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletionWithData;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIChatCompletionWithDataService"/>
/// </summary>
public sealed class AzureOpenAIChatCompletionWithDataTests : IDisposable
{
    private readonly AzureOpenAIChatCompletionWithDataConfig _config;

    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAIChatCompletionWithDataTests()
    {
        this._config = this.GetConfig();

        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient, this._mockLoggerFactory.Object) :
            new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("fake-completion-model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task SpecifiedConfigurationShouldBeUsedAsync()
    {
        // Arrange
        const string ExpectedUri = "https://fake-completion-endpoint/openai/deployments/fake-completion-model-id/extensions/chat/completions?api-version=fake-api-version";
        var service = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);

        // Act
        await service.GetChatMessageContentsAsync([]);

        // Assert
        var actualUri = this._messageHandlerStub.RequestUri?.AbsoluteUri;
        var actualRequestHeaderValues = this._messageHandlerStub.RequestHeaders!.GetValues("Api-Key");
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);

        Assert.Equal(ExpectedUri, actualUri);

        Assert.Contains("fake-completion-api-key", actualRequestHeaderValues);
        Assert.Contains("https://fake-data-source-endpoint", actualRequestContent, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("fake-data-source-api-key", actualRequestContent, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("fake-data-source-index", actualRequestContent, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultApiVersionShouldBeUsedAsync()
    {
        // Arrange
        var config = this.GetConfig();
        config.CompletionApiVersion = string.Empty;

        var service = new AzureOpenAIChatCompletionWithDataService(config, this._httpClient);

        // Act
        await service.GetChatMessageContentsAsync([]);

        // Assert
        var actualUri = this._messageHandlerStub.RequestUri?.AbsoluteUri;

        Assert.Contains("2023-06-01-preview", actualUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task GetChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_with_data_test_response.json"))
        };

        // Act
        var result = await service.GetChatMessageContentsAsync([]);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat with data response", result[0].Content);

        var usage = result[0].Metadata?["Usage"] as ChatWithDataUsage;

        Assert.NotNull(usage);
        Assert.Equal(55, usage.PromptTokens);
        Assert.Equal(100, usage.CompletionTokens);
        Assert.Equal(155, usage.TotalTokens);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_with_data_streaming_test_response.txt")));

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([]))
        {
            Assert.Equal("Test chat with data streaming response", chunk.Content);
        }
    }

    [Fact]
    public async Task GetTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_with_data_test_response.json"))
        };

        // Act
        var result = await service.GetTextContentsAsync("Prompt");

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat with data response", result[0].Text);

        var usage = result[0].Metadata?["Usage"] as ChatWithDataUsage;

        Assert.NotNull(usage);
        Assert.Equal(55, usage.PromptTokens);
        Assert.Equal(100, usage.CompletionTokens);
        Assert.Equal(155, usage.TotalTokens);
    }

    [Fact]
    public async Task GetStreamingTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_with_data_streaming_test_response.txt")));

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        await foreach (var chunk in service.GetStreamingTextContentsAsync("Prompt"))
        {
            Assert.Equal("Test chat with data streaming response", chunk.Text);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private AzureOpenAIChatCompletionWithDataConfig GetConfig()
    {
        return new AzureOpenAIChatCompletionWithDataConfig
        {
            CompletionModelId = "fake-completion-model-id",
            CompletionEndpoint = "https://fake-completion-endpoint",
            CompletionApiKey = "fake-completion-api-key",
            CompletionApiVersion = "fake-api-version",
            DataSourceEndpoint = "https://fake-data-source-endpoint",
            DataSourceApiKey = "fake-data-source-api-key",
            DataSourceIndex = "fake-data-source-index"
        };
    }
}
