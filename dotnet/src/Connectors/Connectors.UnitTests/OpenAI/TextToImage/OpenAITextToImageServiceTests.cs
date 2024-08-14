// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
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
        Assert.False(service.Attributes.ContainsKey("ModelId"));
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
        var service = new OpenAITextToImageService("api-key", "organization", "dall-e-3", this._httpClient);
        Assert.Equal("dall-e-3", service.Attributes["ModelId"]);
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

    [Fact]
    public async Task GetImageContentsAsyncWithValidInputReturnsImageContentsAsync()
    {
        // Arrange
        var service = new OpenAITextToImageService("api-key", "organization", "dall-e-3", this._httpClient);
        Assert.Equal("dall-e-3", service.Attributes["ModelId"]);

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

        var input = new TextContent("A cute baby sea otter");
        var executionSettings = new OpenAITextToImageExecutionSettings
        {
            Width = 1024,
            Height = 1024,
            Quality = "hd",
            Style = "natural",
            ImageCount = 1
        };

        // Act
        var result = await service.GetImageContentsAsync(input, executionSettings);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new Uri("https://image-url"), result[0].Uri);
    }

    [Theory]
    [InlineData(1024, 1024, "hd", "natural", 1, "https://image-url", false)]
    [InlineData(123, 456, "hd", "natural", 1, "", true)]
    [InlineData(1024, 1024, "hd", "natural", 2, "https://image-url1|https://image-url2", false)]
    [InlineData(1024, 1024, "ultra", "natural", 1, "", true)]
    [InlineData(1024, 1024, "hd", "artistic", 1, "", true)]
    public async Task GetImageContentsReturnsExpectedResultsAsync(
        int width,
        int height,
        string quality,
        string style,
        int imageCount,
        string expectedUrls,
        bool expectException)
    {
        // Arrange
        var service = new OpenAITextToImageService("api-key", "organization", "dall-e-3", this._httpClient);

        if (!expectException)
        {
            var urls = expectedUrls.Split('|').Select(url =>
            {
                return url.StartsWith("http", StringComparison.OrdinalIgnoreCase) ?
                    $"{{ \"url\": \"{url}\" }}" :
                    $"{{ \"b64_json\": \"{url}\" }}";
            });
            var jsonResponse = $"{{ \"created\": 1702575371, \"data\": [ {string.Join(",", urls)} ] }}";

            this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(jsonResponse, Encoding.UTF8, "application/json")
            };
        }

        var input = new TextContent("A picturesque landscape");
        var executionSettings = new OpenAITextToImageExecutionSettings
        {
            Width = width,
            Height = height,
            Quality = quality,
            Style = style,
            ImageCount = imageCount
        };

        // Act & Assert
        if (expectException)
        {
            await Assert.ThrowsAsync<NotSupportedException>(async () =>
            {
                await service.GetImageContentsAsync(input, executionSettings);
            });
        }
        else
        {
            var result = await service.GetImageContentsAsync(input, executionSettings);

            Assert.NotNull(result);
            Assert.Equal(imageCount, result.Count);

            var expectedUrlList = expectedUrls.Split('|').ToList();
            for (int i = 0; i < result.Count; i++)
            {
                if (Uri.TryCreate(expectedUrlList[i], UriKind.Absolute, out var uriResult) &&
                    (uriResult.Scheme == Uri.UriSchemeHttp || uriResult.Scheme == Uri.UriSchemeHttps))
                {
                    Assert.Equal(uriResult, result[i].Uri);
                }
                else
                {
                    Assert.StartsWith("data:;base64,", result[i].DataUri);
                    Assert.Contains(expectedUrlList[i], result[i].DataUri);
                }
            }
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
