// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextToAudio;

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
    }

    [Theory]
    [MemberData(nameof(ExecutionSettings))]
    public async Task GetAudioContentWithInvalidSettingsThrowsExceptionAsync(OpenAITextToAudioExecutionSettings? settings, Type expectedExceptionType)
    {
        // Arrange
        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        await using var stream = new MemoryStream(new byte[] { 0x00, 0x00, 0xFF, 0x7F });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var exception = await Record.ExceptionAsync(() => service.GetAudioContentAsync("Some text", settings));

        // Assert
        Assert.NotNull(exception);
        Assert.IsType(expectedExceptionType, exception);
    }

    [Fact]
    public async Task GetAudioContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var expectedByteArray = new byte[] { 0x00, 0x00, 0xFF, 0x7F };

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentAsync("Some text", new OpenAITextToAudioExecutionSettings("voice"));

        // Assert
        Assert.NotNull(result?.Data);
        Assert.True(result.Data.ToArray().SequenceEqual(expectedByteArray));
    }

    [Theory]
    [InlineData(true, "http://local-endpoint")]
    [InlineData(false, "https://api.openai.com")]
    public async Task GetAudioContentUsesValidBaseUrlAsync(bool useHttpClientBaseAddress, string expectedBaseAddress)
    {
        // Arrange
        var expectedByteArray = new byte[] { 0x00, 0x00, 0xFF, 0x7F };

        if (useHttpClientBaseAddress)
        {
            this._httpClient.BaseAddress = new Uri("http://local-endpoint");
        }

        var service = new OpenAITextToAudioService("model-id", "api-key", "organization", this._httpClient);
        await using var stream = new MemoryStream(expectedByteArray);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act
        var result = await service.GetAudioContentAsync("Some text", new OpenAITextToAudioExecutionSettings("voice"));

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
        { null, typeof(ArgumentNullException) },
        { new OpenAITextToAudioExecutionSettings(""), typeof(ArgumentException) },
    };
}
