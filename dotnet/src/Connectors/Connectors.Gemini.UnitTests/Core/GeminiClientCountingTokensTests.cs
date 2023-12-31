#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core;

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
        var client = new GeminiClient(this._httpClient, "fake-api-key", modelId: "fake-model");

        // Act
        var tokenCount = await client.CountTokensAsync("fake-text");

        // Assert
        Assert.True(tokenCount > 0);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
