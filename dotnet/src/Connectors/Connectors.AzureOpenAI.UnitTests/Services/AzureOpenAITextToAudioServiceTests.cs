// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextToAudioService"/> class.
/// </summary>
public sealed class AzureOpenAITextToAudioServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAITextToAudioServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorsAddRequiredMetadata(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id");

        // Assert
        Assert.Equal("model-id", service.Attributes["ModelId"]);
        Assert.Equal("deployment-name", service.Attributes["DeploymentName"]);
    }

    [Fact]
    public void ItThrowsIfModelIdIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AzureOpenAITextToAudioService(null!, "https://endpoint", "api-key"));
        Assert.Throws<ArgumentException>(() => new AzureOpenAITextToAudioService("", "https://endpoint", "api-key"));
        Assert.Throws<ArgumentException>(() => new AzureOpenAITextToAudioService(" ", "https://endpoint", "api-key"));
    }

    [Fact]
    public async Task GetAudioContentWithInvalidSettingsThrowsExceptionAsync()
    {
        // Arrange
        var settingsWithInvalidVoice = new AzureOpenAITextToAudioExecutionSettings("");

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        await using var stream = new MemoryStream(new byte[] { 0x00, 0x00, 0xFF, 0x7F });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(() => service.GetAudioContentsAsync("Some text", settingsWithInvalidVoice));
    }

    [Fact]
    public async Task GetAudioContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var expectedByteArray = new byte[] { 0x00, 0x00, 0xFF, 0x7F };

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings("Nova"));

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

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings(voice) { ResponseFormat = format });

        // Assert
        var requestBody = JsonSerializer.Deserialize<JsonObject>(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestBody);
        Assert.Equal(voice, requestBody["voice"]?.ToString());
        Assert.Equal(format, requestBody["response_format"]?.ToString());

        var audioData = result[0].Data!.Value;
        Assert.False(audioData.IsEmpty);
        Assert.True(audioData.Span.SequenceEqual(expectedByteArray));
    }

    [Fact]
    public async Task GetAudioContentThrowsWhenVoiceIsNotSupportedAsync()
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () => await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings("voice")));
    }

    [Fact]
    public async Task GetAudioContentThrowsWhenFormatIsNotSupportedAsync()
    {
        // Arrange
        byte[] expectedByteArray = [0x00, 0x00, 0xFF, 0x7F];

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () => await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings() { ResponseFormat = "not supported" }));
    }

    [Theory]
    [InlineData(true, "http://local-endpoint")]
    [InlineData(false, "https://endpoint")]
    public async Task GetAudioContentUsesValidBaseUrlAsync(bool useHttpClientBaseAddress, string expectedBaseAddress)
    {
        // Arrange
        var expectedByteArray = new byte[] { 0x00, 0x00, 0xFF, 0x7F };

        if (useHttpClientBaseAddress)
        {
            this._httpClient.BaseAddress = new Uri("http://local-endpoint");
        }

        var service = new AzureOpenAITextToAudioService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings("Nova"));

        // Assert
        Assert.StartsWith(expectedBaseAddress, this._messageHandlerStub.RequestUri!.AbsoluteUri, StringComparison.InvariantCulture);
    }

    [Theory]
    [InlineData("model-1", "model-2", "deployment", "model-2")]
    [InlineData("model-1", null, "deployment", "model-1")]
    [InlineData(null, "model-2", "deployment", "model-2")]
    [InlineData(null, null, "deployment", "deployment")]
    public async Task GetAudioContentPrioritizesModelIdOverDeploymentNameAsync(string? modelInSettings, string? modelInConstructor, string deploymentName, string expectedModel)
    {
        // Arrange
        var expectedByteArray = new byte[] { 0x00, 0x00, 0xFF, 0x7F };

        var service = new AzureOpenAITextToAudioService(deploymentName, "https://endpoint", "api-key", modelInConstructor, this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentsAsync("Some text", new AzureOpenAITextToAudioExecutionSettings("Nova") { ModelId = modelInSettings });

        // Assert
        var requestBody = JsonSerializer.Deserialize<JsonObject>(this._messageHandlerStub.RequestContent!);
        Assert.Equal(expectedModel, requestBody?["model"]?.ToString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
