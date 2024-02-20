// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.CustomClient.Moderation;

[SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "Test code")]
public sealed class OpenAIModerationClientTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./OpenAI/TestData/moderation_response.json";

    public OpenAIModerationClientTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content =
            new StringContent(File.ReadAllText(TestDataFilePath));
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void ConstructorWhenModelIdIsNullOrWhiteSpaceThrowsArgumentException(string? modelId)
    {
        // Act and Assert
        Assert.ThrowsAny<ArgumentException>(() => this.CreateOpenAIModerationClient(modelId: modelId!));
    }

    [Fact]
    public async Task ItUsesEndpointProviderToGetModerationEndpointAsync()
    {
        // Arrange
        var endpointProviderMock = new Mock<IEndpointProvider>();
        endpointProviderMock
            .Setup(p => p.ModerationEndpoint).Returns(new Uri("https://example.com/"));
        var sut = this.CreateOpenAIModerationClient(endpointProvider: endpointProviderMock.Object);

        // Act
        await sut.ClassifyTextAsync("text");

        // Assert
        endpointProviderMock.VerifyAll();
    }

    [Fact]
    public async Task ItCreatesRequestUsingHttpRequestFactoryAsync()
    {
        // Arrange
        var httpRequestFactoryMock = new Mock<IHttpRequestFactory>();
        httpRequestFactoryMock
            .Setup(f => f.CreatePost(It.IsAny<object>(), It.IsAny<Uri>()))
            .Returns(new HttpRequestMessage(HttpMethod.Post, new Uri("https://example.com/")));
        var sut = this.CreateOpenAIModerationClient(httpRequestFactory: httpRequestFactoryMock.Object);

        // Act
        await sut.ClassifyTextAsync("text");

        // Assert
        httpRequestFactoryMock.VerifyAll();
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public async Task WhenTextIsNullOrWhiteSpaceThrowsArgumentExceptionAsync(string? text)
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();

        // Act and Assert
        await Assert.ThrowsAnyAsync<ArgumentException>(() => sut.ClassifyTextAsync(text!));
    }

    private OpenAIModerationClient CreateOpenAIModerationClient(
        HttpClient? httpClient = null,
        string modelId = "modelId",
        IHttpRequestFactory? httpRequestFactory = null,
        IEndpointProvider? endpointProvider = null,
        ILogger? logger = null)
    {
        return new OpenAIModerationClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory ?? new FakeHttpRequestFactory(),
            endpointProvider: endpointProvider ?? new FakeEndpointProvider(),
            logger: logger);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
