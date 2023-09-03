// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletionWithData;

/// <summary>
/// Unit tests for <see cref="AzureChatCompletionWithData"/>
/// </summary>
public sealed class AzureChatCompletionWithDataTests : IDisposable
{
    private AzureChatCompletionWithDataConfig _config;

    private HttpMessageHandlerStub _messageHandlerStub;
    private HttpClient _httpClient;

    public AzureChatCompletionWithDataTests()
    {
        this._config = this.GetConfig();

        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedConfigurationShouldBeUsedAsync()
    {
        // Arrange
        const string expectedUri = "https://fake-completion-endpoint/openai/deployments/fake-completion-model-id/extensions/chat/completions?api-version=fake-api-version";
        var chatCompletion = new AzureChatCompletionWithData(this._config, this._httpClient);

        // Act
        await chatCompletion.GetChatCompletionsAsync(new ChatHistory());

        // Assert
        var actualUri = this._messageHandlerStub.RequestUri?.AbsoluteUri;
        var actualRequestHeaderValues = this._messageHandlerStub.RequestHeaders!.GetValues("Api-Key");
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);

        Assert.Equal(expectedUri, actualUri);

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

        var chatCompletion = new AzureChatCompletionWithData(config, this._httpClient);

        // Act
        await chatCompletion.GetChatCompletionsAsync(new ChatHistory());

        // Assert
        var actualUri = this._messageHandlerStub.RequestUri?.AbsoluteUri;

        Assert.Contains("2023-06-01-preview", actualUri, StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private AzureChatCompletionWithDataConfig GetConfig()
    {
        return new AzureChatCompletionWithDataConfig
        {
            CompletionModelId = "fake-completion-model-id",
            CompletionEndpoint = "https://fake-completion-endpoint",
            CompletionApiKey = "fake-completion-api-key",
            CompletionApiVersion = "fake-api-version",
            DataSourceEndpoint = "https://fake-data-source-endpoint",
            DataSourceApiKey = "fake-data-source-api-key",
            DataSourceIndex = "fake-data-source-index",
            ResponsibleAIPolicy = "fake-policy",
        };
    }
}
