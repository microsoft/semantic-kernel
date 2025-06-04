// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using OpenAI;
using Xunit;

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

    [Fact]
    public void ItThrowsIfModelIdIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new OpenAIAudioToTextService(" ", "apikey"));
        Assert.Throws<ArgumentException>(() => new OpenAIAudioToTextService(" ", openAIClient: new(new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentException>(() => new OpenAIAudioToTextService("", "apikey"));
        Assert.Throws<ArgumentException>(() => new OpenAIAudioToTextService("", openAIClient: new(new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentNullException>(() => new OpenAIAudioToTextService(null!, "apikey"));
        Assert.Throws<ArgumentNullException>(() => new OpenAIAudioToTextService(null!, openAIClient: new(new ApiKeyCredential("apikey"))));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient(new ApiKeyCredential("key"));
        var service = includeLoggerFactory ?
            new OpenAIAudioToTextService("model-id", client, loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIAudioToTextService("model-id", client);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", "organization", this._httpClient);
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
    public async Task GetTextContentThrowsIfAudioCantBeReadAsync()
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", "organization", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => { await service.GetTextContentsAsync(new AudioContent(new Uri("http://remote-audio")), new OpenAIAudioToTextExecutionSettings("file.mp3")); });
    }

    [Fact]
    public async Task GetTextContentThrowsIfFileNameIsInvalidAsync()
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", "organization", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => { await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), new OpenAIAudioToTextExecutionSettings("invalid")); });
    }

    [Theory]
    [InlineData(new[] { "word" }, new[] { "word" })]
    [InlineData(new[] { "word", "Word", "wOrd", "Segment" }, new[] { "word", "segment" })]
    [InlineData(new[] { "Word", "Segment" }, new[] { "word", "segment" })]
    [InlineData(new[] { "Segment" }, new[] { "segment" })]
    [InlineData(new[] { "Segment", "wOrd" }, new[] { "word", "segment" })]
    [InlineData(new[] { "WORD" }, new[] { "word" })]
    [InlineData(new string[] { }, null)]
    [InlineData(null, null)]
    public async Task GetTextContentGranularitiesWorksCorrectlyAsync(string[]? granularities, string[]? expectedGranularities)
    {
        // Arrange
        var service = new OpenAIAudioToTextService("model-id", "api-key", "organization", this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), new OpenAIAudioToTextExecutionSettings("file.mp3")
        {
            ResponseFormat = "verbose_json",
            TimestampGranularities = granularities
        });

        // Assert
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        if (granularities is null || granularities.Length == 0)
        {
            Assert.DoesNotContain("timestamp_granularities[]", requestBody);
        }
        else
        {
            foreach (var granularity in expectedGranularities!)
            {
                Assert.Contains($"Content-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\n{granularity}", requestBody);
            }
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
