// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
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

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentAsync(new AudioContent(new BinaryData("data")), new OpenAIAudioToTextExecutionSettings("file.mp3"));

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result.Text);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<OpenAIAudioToTextExecutionSettings?, Type> ExecutionSettings => new()
    {
        { null, typeof(ArgumentNullException) },
        { new OpenAIAudioToTextExecutionSettings(""), typeof(ArgumentException) },
        { new OpenAIAudioToTextExecutionSettings("file"), typeof(ArgumentException) }
    };
}
