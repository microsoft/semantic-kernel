// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using OpenAI;
using Xunit;
using static Microsoft.SemanticKernel.Connectors.OpenAI.OpenAIAudioToTextExecutionSettings;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAIAudioToTextService"/> class.
/// </summary>
public sealed class OpenAIAudioToTextServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAIAudioToTextServiceTests()
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
            new OpenAIAudioToTextService("model-id", "api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIAudioToTextService("model-id", "api-key", "organization");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient("key");
        var service = includeLoggerFactory ?
            new OpenAIAudioToTextService("model-id", client, loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIAudioToTextService("model-id", client);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Default }, "0")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Word }, "word")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Segment }, "segment")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Segment, TimeStampGranularities.Word }, "word", "segment")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Word, TimeStampGranularities.Segment }, "word", "segment")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Default, TimeStampGranularities.Word }, "word", "0")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Word, TimeStampGranularities.Default }, "word", "0")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Default, TimeStampGranularities.Segment }, "segment", "0")]
    [InlineData(new TimeStampGranularities[] { TimeStampGranularities.Segment, TimeStampGranularities.Default }, "segment", "0")]
    public async Task GetTextContentGranularitiesWorksAsync(TimeStampGranularities[] granularities, params string[] expectedGranularities)
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var settings = new OpenAIAudioToTextExecutionSettings("file.mp3") { Granularities = granularities };
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        Assert.NotNull(result);

        var multiPartData = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var multiPartBreak = multiPartData.Substring(0, multiPartData.IndexOf("\r\n", StringComparison.OrdinalIgnoreCase));

        foreach (var granularity in expectedGranularities)
        {
            var expectedMultipart = $"{granularity}\r\n{multiPartBreak}";
            Assert.Contains(expectedMultipart, multiPartData);
        }
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", "organization", null, this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), new OpenAIAudioToTextExecutionSettings("file.mp3"));

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result[0].Text);
    }

    [Fact]
    public async Task GetTextContentsDoesLogActionAsync()
    {
        // Assert
        var modelId = "whisper-1";
        var logger = new Mock<ILogger<OpenAITextToAudioService>>();
        logger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        this._mockLoggerFactory.Setup(x => x.CreateLogger(It.IsAny<string>())).Returns(logger.Object);

        // Arrange
        var sut = new OpenAIAudioToTextService(modelId, "apiKey", httpClient: this._httpClient, loggerFactory: this._mockLoggerFactory.Object);

        // Act
        await sut.GetTextContentsAsync(new(new byte[] { 0x01, 0x02 }, "text/plain"));

        // Assert
        logger.VerifyLog(LogLevel.Information, $"Action: {nameof(OpenAIAudioToTextService.GetTextContentsAsync)}. OpenAI Model ID: {modelId}.", Times.Once());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
