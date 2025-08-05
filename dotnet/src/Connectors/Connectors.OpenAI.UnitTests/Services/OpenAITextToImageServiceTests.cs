// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
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

    // Add these tests to OpenAITextToImageServiceTests.cs

    [Fact]
    public async Task EditImageWorksCorrectlyAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-response.json"))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient) as IImageToImageService;
        Assert.NotNull(sut);

        using var imageStream = new MemoryStream(Encoding.UTF8.GetBytes("fake image data"));

        // Act
        var result = await sut.EditImageAsync(imageStream, "make the sky purple");

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new Uri("https://image-url/"), result[0].Uri);
    }

    [Fact]
    public async Task EditImageWithMaskWorksCorrectlyAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-response.json"))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient) as IImageToImageService;
        Assert.NotNull(sut);

        using var imageStream = new MemoryStream(Encoding.UTF8.GetBytes("fake image data"));
        using var maskStream = new MemoryStream(Encoding.UTF8.GetBytes("fake mask data"));

        // Act
        var result = await sut.EditImageAsync(imageStream, "add a rainbow", maskStream);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new Uri("https://image-url/"), result[0].Uri);
    }

    [Theory]
    [InlineData(1, "./TestData/text-to-image-response.json")]
    [InlineData(3, "./TestData/text-to-image-3-images-response.json")]
    [InlineData(5, "./TestData/text-to-image-5-images-response.json")]
    public async Task EditImageWithMultipleOutputsWorksCorrectlyAsync(int numberOfImages, string responseFile)
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText(responseFile))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient) as IImageToImageService;
        Assert.NotNull(sut);

        using var imageStream = new MemoryStream(Encoding.UTF8.GetBytes("fake image data"));

        // Act
        var result = await sut.EditImageAsync(
            imageStream,
            "make it colorful",
            executionSettings: new OpenAITextToImageExecutionSettings { NumberOfImages = numberOfImages });

        // Assert
        Assert.NotNull(result);
        Assert.Equal(numberOfImages, result.Count);
        for (int i = 0; i < numberOfImages; i++)
        {
            Assert.NotNull(result[i].Uri);
        }
    }

    [Theory]
    [InlineData("low", "low")]
    [InlineData("medium", "medium")]
    [InlineData("high", "high")]
    public async Task GptImage1QualityRequestWorksCorrectlyAsync(string quality, string expectedQuality)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: "gpt-image-1", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { Quality = quality });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains($"\"quality\":\"{expectedQuality}\"", requestBody);
    }

    [Theory]
    [InlineData("auto", "auto")]
    [InlineData("low", "low")]
    public async Task GptImage1ModerationRequestWorksCorrectlyAsync(string moderation, string expectedModeration)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: "gpt-image-1", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { Moderation = moderation });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains($"\"moderation\":\"{expectedModeration}\"", requestBody);
    }

    [Theory]
    [InlineData("png", "png")]
    [InlineData("jpeg", "jpeg")]
    [InlineData("webp", "webp")]
    public async Task GptImage1OutputFormatRequestWorksCorrectlyAsync(string format, string expectedFormat)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: "gpt-image-1", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("my prompt", new OpenAITextToImageExecutionSettings { OutputFormat = format });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains($"\"output_format\":\"{expectedFormat}\"", requestBody);
    }

    [Theory]
    [InlineData(1, "./TestData/text-to-image-response.json")]
    [InlineData(2, "./TestData/text-to-image-multiple-response.json")]
    [InlineData(4, "./TestData/text-to-image-4-images-response.json")]
    [InlineData(10, "./TestData/text-to-image-10-images-response.json")]
    public async Task GetImageContentsWithMultipleImagesWorksCorrectlyAsync(int numberOfImages, string responseFile)
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText(responseFile))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync(
            "generate multiple images",
            new OpenAITextToImageExecutionSettings { NumberOfImages = numberOfImages });

        // Assert
        Assert.NotNull(result);
        Assert.Equal(numberOfImages, result.Count);
        for (int i = 0; i < numberOfImages; i++)
        {
            Assert.NotNull(result[i].Uri);
            Assert.NotNull(result[i].InnerContent);
            Assert.IsType<GeneratedImage>(result[i].InnerContent);
        }
    }

    [Theory]
    [InlineData(1, "./TestData/text-to-image-b64_json-format-response.json")]
    [InlineData(2, "./TestData/text-to-image-2-images-b64-response.json")]
    [InlineData(4, "./TestData/text-to-image-4-images-b64-response.json")]
    public async Task GetImageContentsWithMultipleBytesImagesWorksCorrectlyAsync(int numberOfImages, string responseFile)
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText(responseFile))
        };

        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync(
            "generate multiple images",
            new OpenAITextToImageExecutionSettings
            {
                NumberOfImages = numberOfImages,
                ResponseFormat = "b64_json"
            });

        // Assert
        Assert.NotNull(result);
        Assert.Equal(numberOfImages, result.Count);
        for (int i = 0; i < numberOfImages; i++)
        {
            Assert.True(result[i].CanRead);
            Assert.Equal("image/png", result[i].MimeType);
            Assert.NotNull(result[i].InnerContent);
            Assert.IsType<GeneratedImage>(result[i].InnerContent);

            var breakingGlass = result[i].InnerContent as GeneratedImage;
            // For the single b64_json file, the revised prompt is just "my prompt", not "my prompt 0"
            var expectedPrompt = numberOfImages == 1 ? "my prompt" : $"my prompt {i}";
            Assert.Equal(expectedPrompt, breakingGlass!.RevisedPrompt);
        }
    }

    [Theory]
    [InlineData("dall-e-2")]
    [InlineData("dall-e-3")]
    [InlineData("gpt-image-1")]
    public async Task GetImageContentsWithDifferentModelsWorksCorrectlyAsync(string modelId)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: modelId, httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("test prompt");

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new Uri("https://image-url/"), result[0].Uri);
        Assert.Equal(modelId, sut.Attributes["ModelId"]);
    }

    [Fact]
    public async Task GetImageContentsValidatesInputAsync()
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() =>
            sut.GetImageContentsAsync(null!));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    [InlineData(-10)]
    public async Task GetImageContentsWithInvalidNumberOfImagesThrowsAsync(int invalidNumber)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", httpClient: this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            sut.GetImageContentsAsync("test", new OpenAITextToImageExecutionSettings { NumberOfImages = invalidNumber }));
    }

    [Theory]
    [InlineData("standard", "dall-e-2")]
    [InlineData("hd", "dall-e-3")]
    [InlineData("low", "gpt-image-1")]
    [InlineData("medium", "gpt-image-1")]
    [InlineData("high", "gpt-image-1")]
    public async Task GetImageContentsWithQualitySettingsWorksCorrectlyAsync(string quality, string modelId)
    {
        // Arrange
        var sut = new OpenAITextToImageService("api-key", modelId: modelId, httpClient: this._httpClient);

        // Act
        var result = await sut.GetImageContentsAsync("test prompt", new OpenAITextToImageExecutionSettings { Quality = quality });

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        if (string.Equals(modelId, "gpt-image-1", StringComparison.OrdinalIgnoreCase))
        {
            Assert.Contains($"\"quality\":\"{quality.ToLowerInvariant()}\"", requestBody);
        }
        else
        {
            var expectedQuality = string.Equals(quality.ToLowerInvariant(), "hd", StringComparison.Ordinal) ? "hd" : "standard";
            Assert.Contains($"\"quality\":\"{expectedQuality}\"", requestBody);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
