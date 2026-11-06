// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToImage;
using Moq;
using OpenAI.Images;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

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
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-to-image-response.json"))
            }
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ConstructorWorksCorrectly()
    {
        // Arrange & Act
        var sut = new OpenAITextToImageService("apiKey", "organization", "model");

        // Assert
        Assert.NotNull(sut);
        Assert.Equal("organization", sut.Attributes[ClientCore.OrganizationKey]);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(256, 256, "dall-e-2")]
    [InlineData(512, 512, "dall-e-2")]
    [InlineData(1024, 1024, "dall-e-2")]
    [InlineData(1024, 1024, "dall-e-3")]
    [InlineData(1024, 1792, "dall-e-3")]
    [InlineData(1792, 1024, "dall-e-3")]
    [InlineData(123, 321, "custom-model-1")]
    [InlineData(179, 124, "custom-model-2")]
    public async Task GenerateImageWorksCorrectlyAsync(int width, int height, string modelId)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: modelId, httpClient: this._httpClient);
        Assert.Equal(modelId, sut.Attributes["ModelId"]);

        // Act 
        var result = await sut.GenerateImageAsync("description", width, height);

        // Assert
        Assert.Equal("https://image-url/", result);
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("uri", "url")]
    [InlineData("url", "url")]
    [InlineData("GeneratedImage.Uri", "url")]
    [InlineData("bytes", "b64_json")]
    [InlineData("b64_json", "b64_json")]
    [InlineData("GeneratedImage.Bytes", "b64_json")]
    public async Task GetUriImageContentsResponseFormatRequestWorksCorrectlyAsync(string? responseFormatOption, string? expectedResponseFormat)
    {
        // Arrange
        object? responseFormatObject = null;

        switch (responseFormatOption)
        {
            case "GeneratedImage.Uri": responseFormatObject = GeneratedImageFormat.Uri; break;
            case "GeneratedImage.Bytes": responseFormatObject = GeneratedImageFormat.Bytes; break;
            default: responseFormatObject = responseFormatOption; break;
        }

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { ResponseFormat = responseFormatObject });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        if (expectedResponseFormat is not null)
        {
            Assert.Contains($"\"response_format\":\"{expectedResponseFormat}\"", requestBody);
        }
        else
        {
            // Then no response format is provided, it should not be included in the request body
            Assert.DoesNotContain("response_format", requestBody);
        }
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("hd", "hd")]
    [InlineData("high", "hd")]
    [InlineData("standard", "standard")]
    [InlineData("medium", "medium")]
    [InlineData("low", "low")]
    [InlineData("auto", "auto")]
    public async Task GetUriImageContentsImageQualityRequestWorksCorrectlyAsync(string? quality, string? expectedQuality)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { Quality = quality });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        if (expectedQuality is not null)
        {
            Assert.Contains($"\"quality\":\"{expectedQuality}\"", requestBody);
        }
        else
        {
            // Then no quality is provided, it should not be included in the request body
            Assert.DoesNotContain("quality", requestBody);
        }
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("vivid", "vivid")]
    [InlineData("natural", "natural")]
    public async Task GetUriImageContentsImageStyleRequestWorksCorrectlyAsync(string? style, string? expectedStyle)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { Style = style });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        if (expectedStyle is not null)
        {
            Assert.Contains($"\"style\":\"{expectedStyle}\"", requestBody);
        }
        else
        {
            // Then no style is provided, it should not be included in the request body
            Assert.DoesNotContain("style", requestBody);
        }
    }

    [Theory]
    [InlineData(null, null, null)]
    [InlineData(1, 2, "1x2")]
    public async Task GetUriImageContentsImageSizeRequestWorksCorrectlyAsync(int? width, int? height, string? expectedSize)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings
        {
            Size = width.HasValue && height.HasValue
            ? (width.Value, height.Value)
            : null
        });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        if (expectedSize is not null)
        {
            Assert.Contains($"\"size\":\"{expectedSize}\"", requestBody);
        }
        else
        {
            // Then no size is provided, it should not be included in the request body
            Assert.DoesNotContain("size", requestBody);
        }
    }

    [Fact]
    public async Task GetByteImageContentsResponseWorksCorrectlyAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-b64_json-format-response.json"))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { ResponseFormat = "b64_json" });

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        var imageContent = result[0];
        Assert.NotNull(imageContent);
        Assert.True(imageContent.CanRead);
        Assert.Equal("image/png", imageContent.MimeType);
        Assert.NotNull(imageContent.InnerContent);
        Assert.IsType<GeneratedImage>(imageContent.InnerContent);

        var breakingGlass = imageContent.InnerContent as GeneratedImage;
        Assert.Equal("my prompt", breakingGlass!.RevisedPrompt);
    }

    [Fact]
    public async Task GetUrlImageContentsResponseWorksCorrectlyAsync()
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { ResponseFormat = "url" });

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        var imageContent = result[0];
        Assert.NotNull(imageContent);
        Assert.False(imageContent.CanRead);
        Assert.Equal(new Uri("https://image-url/"), imageContent.Uri);
        Assert.NotNull(imageContent.InnerContent);
        Assert.IsType<GeneratedImage>(imageContent.InnerContent);

        var breakingGlass = imageContent.InnerContent as GeneratedImage;
        Assert.Equal("my prompt", breakingGlass!.RevisedPrompt);
    }

    [Fact]
    public async Task GenerateGptImageReturnsDataUriAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-b64_json-format-response.json"))
        };
        this._messageHandlerStub.ResponseToReturn = responseMessage;
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GenerateImageAsync("A sea otter", 1024, 1024);

        // Assert
        Assert.Equal("data:image/png;base64,iVBORw0KGgoAAA==", result);
    }

    [Fact]
    public async Task GetGptImageContentsPreservesSettingsAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-b64_json-format-response.json"))
        };
        this._messageHandlerStub.ResponseToReturn = responseMessage;
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("A sea otter", new OpenAITextToImageExecutionSettings
        {
            Size = (1536, 1024),
            Quality = "low",
            EndUserId = "test-user"
        });

        // Assert
        var image = Assert.Single(result);
        Assert.Equal(Convert.FromBase64String("iVBORw0KGgoAAA=="), image.Data!.Value.ToArray());
        Assert.Equal("image/png", image.MimeType);
        Assert.Equal("my prompt", Assert.IsType<GeneratedImage>(image.InnerContent).RevisedPrompt);
        using var request = JsonDocument.Parse(this._messageHandlerStub.RequestContent!);
        Assert.Equal("gpt-image-1", request.RootElement.GetProperty("model").GetString());
        Assert.Equal("A sea otter", request.RootElement.GetProperty("prompt").GetString());
        Assert.Equal("1536x1024", request.RootElement.GetProperty("size").GetString());
        Assert.Equal("low", request.RootElement.GetProperty("quality").GetString());
        Assert.Equal("test-user", request.RootElement.GetProperty("user").GetString());
        Assert.Equal(1, request.RootElement.GetProperty("n").GetInt32());
        Assert.False(request.RootElement.TryGetProperty("response_format", out _));
    }

    [Fact]
    public async Task GetImageContentsPreservesHttpErrorsAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.BadRequest)
        {
            Content = new StringContent("""{"error":{"message":"Invalid image request","type":"invalid_request_error","code":"invalid_parameter"}}""")
        };
        this._messageHandlerStub.ResponseToReturn = responseMessage;
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => sut.GetImageContentsAsync("A sea otter"));
        Assert.Equal(HttpStatusCode.BadRequest, exception.StatusCode);
        Assert.Contains("Invalid image request", exception.Message);
    }

    [Fact]
    public async Task GetImageContentsPropagatesCancellationAsync()
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);
        var cancellationToken = new CancellationToken(canceled: true);

        // Act & Assert
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => sut.GetImageContentsAsync("A sea otter", cancellationToken: cancellationToken));
    }

    [Fact]
    public async Task GetImageContentsRejectsEmptyResponsesAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"created":1726234481,"data":[]}""")
        };
        this._messageHandlerStub.ResponseToReturn = responseMessage;
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => sut.GetImageContentsAsync("A sea otter"));
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
