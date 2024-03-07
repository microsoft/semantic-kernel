// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.Clients;

public sealed class GeminiCountingTokensTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/counttokens_response.json";

    public GeminiCountingTokensTests()
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
        var client = this.CreateTokenCounterClient();

        // Act
        var tokenCount = await client.CountTokensAsync("fake-text");

        // Assert
        Assert.True(tokenCount > 0);
    }

    [Fact]
    public async Task ShouldCallGetCountEndpointAsync()
    {
        // Arrange
        var endpointProviderMock = new Mock<IEndpointProvider>();
        endpointProviderMock.Setup(x => x.GetCountTokensEndpoint(It.IsAny<string>()))
            .Returns(new Uri("https://fake-endpoint.com/"));
        var sut = this.CreateTokenCounterClient(endpointProvider: endpointProviderMock.Object);

        // Act
        await sut.CountTokensAsync("fake-text");

        // Assert
        endpointProviderMock.VerifyAll();
    }

    [Fact]
    public async Task ShouldCallCreatePostRequestAsync()
    {
        // Arrange
        var requestFactoryMock = new Mock<IHttpRequestFactory>();
        requestFactoryMock.Setup(x => x.CreatePost(It.IsAny<object>(), It.IsAny<Uri>()))
#pragma warning disable CA2000
            .Returns(new HttpRequestMessage(HttpMethod.Post, new Uri("https://fake-endpoint.com/")));
#pragma warning restore CA2000
        var sut = this.CreateTokenCounterClient(httpRequestFactory: requestFactoryMock.Object);

        // Act
        await sut.CountTokensAsync("fake-text");

        // Assert
        requestFactoryMock.VerifyAll();
    }

    private GeminiTokenCounterClient CreateTokenCounterClient(
        string modelId = "fake-model",
        IEndpointProvider? endpointProvider = null,
        IHttpRequestFactory? httpRequestFactory = null)
    {
        var client = new GeminiTokenCounterClient(
            httpClient: this._httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory ?? new FakeHttpRequestFactory(),
            endpointProvider: endpointProvider ?? new FakeEndpointProvider());
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
