// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Contents;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AudioToText;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIAudioToTextService"/> class.
/// </summary>
public sealed class AzureOpenAIAudioToTextServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAIAudioToTextServiceTests()
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
            new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithTokenCredentialWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var service = includeLoggerFactory ?
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", credentials, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", credentials, "model-id");

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
            new AzureOpenAIAudioToTextService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment", client, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [MemberData(nameof(ExecutionSettings))]
    public async Task GetTextContentWithInvalidSettingsThrowsExceptionAsync(OpenAIAudioToTextExecutionSettings? settings, Type expectedExceptionType)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var exception = await Record.ExceptionAsync(() => service.GetTextContentAsync(new AudioContent(new BinaryData("data")), settings));

        // Assert
        Assert.NotNull(exception);
        Assert.IsType(expectedExceptionType, exception);
    }

    [Theory]
    [MemberData(nameof(ValidAudioContents))]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync(AudioContent audioContent, string expectedData)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentAsync(audioContent, new OpenAIAudioToTextExecutionSettings("file.mp3"));

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result.Text);

        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        Assert.Contains(expectedData, requestContent, StringComparison.InvariantCulture);
    }

    [Theory]
    [MemberData(nameof(InvalidAudioContents))]
    public async Task GetTextContentWithNullAudioContentThrowsArgumentNullExceptionAsync(AudioContent? audioContent)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() => service.GetTextContentAsync(audioContent!));
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<OpenAIAudioToTextExecutionSettings?, Type> ExecutionSettings => new()
    {
        { new OpenAIAudioToTextExecutionSettings(""), typeof(ArgumentException) },
        { new OpenAIAudioToTextExecutionSettings("file"), typeof(ArgumentException) }
    };

    public static TheoryData<AudioContent, string> ValidAudioContents => new()
    {
        { new AudioContent(new BinaryData("binary-data")), "binary-data" },
        { new AudioContent(new BinaryData("stream").ToStream()), "stream" },
        { new AudioContent(new BinaryData("binary-data")) { Stream = new BinaryData("stream").ToStream() }, "binary-data" },
    };

    public static TheoryData<AudioContent?> InvalidAudioContents => new()
    {
        { null },
        { new AudioContent((BinaryData)null!) },
        { new AudioContent((Stream)null!) }
    };
}
