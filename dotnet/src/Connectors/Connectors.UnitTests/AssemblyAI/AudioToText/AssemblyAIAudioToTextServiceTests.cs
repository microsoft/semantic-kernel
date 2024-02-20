// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Contents;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.AssemblyAI.AudioToText;

/// <summary>
/// Unit tests for <see cref="OpenAIAudioToTextService"/> class.
/// </summary>
public sealed class AssemblyAIAudioToTextServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AssemblyAIAudioToTextServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public void ConstructorWithHttpClientWorksCorrectly()
    {
        // Arrange & Act
        var service = new AssemblyAIAudioToTextService("api-key", this._httpClient);

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentAsync(
            new AudioContent(new BinaryData("data"))
        );

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result.Text);
    }

    [Fact]
    public async Task GetTextContentByStreamWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        using var ms = new MemoryStream();

        // Act
        var result = await service.GetTextContentAsync(ms);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result.Text);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
