// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using Moq;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextToImage;

/// <summary>
/// Unit tests for <see cref="OpenAITextToImageService"/> class.
/// </summary>
public sealed class OpenAITextToImageServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAITextToImageServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ConstructorWorksCorrectly()
    {
        // Arrange & Act
        var sut = new OpenAITextToImageService("api-key", "organization");

        // Assert
        Assert.NotNull(sut);
        Assert.Equal("organization", sut.Attributes[ClientCore.OrganizationKey]);
        Assert.False(sut.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
    }

    [Fact]
    public void OpenAIClientConstructorWorksCorrectly()
    {
        // Arrange
        var sut = new OpenAITextToImageService("model", new OpenAIClient("apikey"));

        // Assert
        Assert.NotNull(sut);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(256, 256)]
    [InlineData(512, 512)]
    [InlineData(1024, 1024)]
    public async Task GenerateImageWorksCorrectlyAsync(int width, int height)
    {
        // Arrange
        var sut = new OpenAITextToImageService("dall-e-3", "api-key", httpClient: this._httpClient);
        Assert.Equal("dall-e-3", sut.Attributes["ModelId"]);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("""
                                        {
                                            "created": 1702575371,
                                            "data": [
                                                {
                                                    "url": "https://image-url"
                                                }
                                            ]
                                        }
                                        """, Encoding.UTF8, "application/json")
        };

        // Act 
        var result = await sut.GenerateImageAsync("description", width, height);

        // Assert
        Assert.Equal("https://image-url", result);
    }

    [Theory]
    [InlineData(123, 456)]
    [InlineData(256, 512)]
    public async Task GenerateImageThrowsWhenSizeIsNotSupportedAsync(int width, int height)
    {
        // Arrange
        var sut = new OpenAITextToImageService("model", "apiKey");

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => sut.GenerateImageAsync("description", width, height));
    }

    [Theory]
    [InlineData(123, 456)]
    [InlineData(256, 512)]
    [InlineData(6546, 545)]
    [InlineData(16, 32)]
    public async Task GenerateImageAllowCustomSizeWhenNonDefaultEndpointIsUsedAsync(int width, int height)
    {
        // Arrange
        var sut = new OpenAITextToImageService("model", endpoint: new Uri("http://localhost"), httpClient: this._httpClient);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("""
                                        {
                                            "created": 1702575371,
                                            "data": [
                                                {
                                                    "url": "https://image-url"
                                                }
                                            ]
                                        }
                                        """, Encoding.UTF8, "application/json")
        };

        // Act 
        var result = await sut.GenerateImageAsync("description", width, height);

        // Assert
        Assert.Equal("https://image-url", result);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
