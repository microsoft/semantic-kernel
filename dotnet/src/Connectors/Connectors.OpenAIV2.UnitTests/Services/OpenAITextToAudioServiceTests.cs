// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAITextToAudioService"/> class.
/// </summary>
public sealed class OpenAITextToAudioServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAITextToAudioServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAITextToAudioService("model-id", "api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAITextToAudioService("model-id", "api-key", "organization");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
        Assert.Equal("Organization", OpenAITextToAudioService.OrganizationKey);
    }

    [Fact]
    public void ItThrowsIfModelIdIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new OpenAITextToAudioService(" ", "apikey"));
        Assert.Throws<ArgumentException>(() => new OpenAITextToAudioService("", "apikey"));
        Assert.Throws<ArgumentNullException>(() => new OpenAITextToAudioService(null!, "apikey"));
    }

    [Theory]
    [MemberData(nameof(ExecutionSettings))]
    public async Task GetAudioContentWithInvalidSettingsThrowsExceptionAsync(OpenAITextToAudioExecutionSettings? settings, Type expectedExceptionType)
    {
        // Arrange
        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream([0x00, 0x00, 0xFF, 0x7F]);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var exception = await Assert.ThrowsAnyAsync<Exception>(async () => await service.GetAudioContentsAsync("Some text", settings));

        // Assert
        Assert.NotNull(exception);
        Assert.IsType(expectedExceptionType, exception);
    }

    [Fact]
    public async Task GetAudioContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text");

        // Assert
        var audioData = result[0].Data!.Value;
        Assert.False(audioData.IsEmpty);
        Assert.True(audioData.Span.SequenceEqual(expectedByteArray));
    }

    [Theory]
    [InlineData("echo", "wav")]
    [InlineData("fable", "opus")]
    [InlineData("onyx", "flac")]
    [InlineData("nova", "aac")]
    [InlineData("shimmer", "pcm")]
    public async Task GetAudioContentVoicesWorksCorrectlyAsync(string voice, string format)
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text", new OpenAITextToAudioExecutionSettings(voice) { ResponseFormat = format });

        // Assert
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var audioData = result[0].Data!.Value;
        Assert.Contains($"\"voice\":\"{voice}\"", requestBody);
        Assert.Contains($"\"response_format\":\"{format}\"", requestBody);
        Assert.False(audioData.IsEmpty);
        Assert.True(audioData.Span.SequenceEqual(expectedByteArray));
    }

    [Fact]
    public async Task GetAudioContentThrowsWhenVoiceIsNotSupportedAsync()
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () => await service.GetAudioContentsAsync("Some text", new OpenAITextToAudioExecutionSettings("voice")));
    }

    [Fact]
    public async Task GetAudioContentThrowsWhenFormatIsNotSupportedAsync()
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () => await service.GetAudioContentsAsync("Some text", new OpenAITextToAudioExecutionSettings() { ResponseFormat = "not supported" }));
    }

    [Theory]
    [InlineData(true, "http://local-endpoint")]
    [InlineData(false, "https://api.openai.com")]
    public async Task GetAudioContentUsesValidBaseUrlAsync(bool useHttpClientBaseAddress, string expectedBaseAddress)
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        if (useHttpClientBaseAddress)
        {
            this._httpClient.BaseAddress = new Uri("http://local-endpoint");
        }

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text");

        // Assert
        Assert.StartsWith(expectedBaseAddress, this._messageHandlerStub.RequestUri!.AbsoluteUri, StringComparison.InvariantCulture);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<OpenAITextToAudioExecutionSettings?, Type> ExecutionSettings => new()
    {
        { new OpenAITextToAudioExecutionSettings("invalid"), typeof(NotSupportedException) },
    };
}
