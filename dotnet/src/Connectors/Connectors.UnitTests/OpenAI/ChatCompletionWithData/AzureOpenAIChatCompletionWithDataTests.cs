// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
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

    public AzureOpenAIChatCompletionWithDataTests()
    {
        this._config = this.GetConfig();

        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedConfigurationShouldBeUsedAsync()
    {
        // Arrange
        const string ExpectedUri = "https://fake-completion-endpoint/openai/deployments/fake-completion-model-id/extensions/chat/completions?api-version=fake-api-version";
        var chatCompletion = new AzureOpenAIChatCompletionWithDataService(this._config, this._httpClient);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(new ChatHistory());

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

        var chatCompletion = new AzureOpenAIChatCompletionWithDataService(config, this._httpClient);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(new ChatHistory());

        // Assert
        var actualUri = this._messageHandlerStub.RequestUri?.AbsoluteUri;

        Assert.Contains("2023-06-01-preview", actualUri, StringComparison.OrdinalIgnoreCase);
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
