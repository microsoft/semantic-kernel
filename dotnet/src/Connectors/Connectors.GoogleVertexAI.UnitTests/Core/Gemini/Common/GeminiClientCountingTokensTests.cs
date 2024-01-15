// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.Common;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.GoogleAI;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.Common;

public sealed class GeminiClientCountingTokensTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/counttokens_response.json";

    public GeminiClientCountingTokensTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldReturnGreaterThanZeroTokenCountAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = this.CreateTokenCounterClient(geminiConfiguration);

        // Act
        var tokenCount = await client.CountTokensAsync("fake-text");

        // Assert
        Assert.True(tokenCount > 0);
    }

    private GeminiTokenCounterClient CreateTokenCounterClient(GeminiConfiguration geminiConfiguration)
    {
        var client = new GeminiTokenCounterClient(
            httpClient: this._httpClient,
            configuration: geminiConfiguration,
            httpRequestFactory: new GoogleAIGeminiHttpRequestFactory(),
            endpointProvider: new GoogleAIGeminiEndpointProvider(geminiConfiguration.ApiKey));
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
