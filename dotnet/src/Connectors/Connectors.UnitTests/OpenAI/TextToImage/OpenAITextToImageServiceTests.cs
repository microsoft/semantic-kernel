// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
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

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAITextToImageService("api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAITextToImageService("api-key", "organization");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("organization", service.Attributes["Organization"]);
    }

    [Theory]
    [InlineData(123, 456, true)]
    [InlineData(256, 512, true)]
    [InlineData(256, 256, false)]
    [InlineData(512, 512, false)]
    [InlineData(1024, 1024, false)]
    public async Task GenerateImageWorksCorrectlyAsync(int width, int height, bool expectedException)
    {
        // Arrange
        var service = new OpenAITextToImageService("api-key", "organization", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"{
                                            ""created"": 1702575371,
                                            ""data"": [
                                                {
                                                    ""url"": ""https://image-url""
                                                }
                                            ]
                                        }", Encoding.UTF8, "application/json")
        };

        // Act & Assert
        if (expectedException)
        {
            await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => service.GenerateImageAsync("description", width, height));
        }
        else
        {
            var result = await service.GenerateImageAsync("description", width, height);

            Assert.Equal("https://image-url", result);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
