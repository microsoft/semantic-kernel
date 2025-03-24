// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Embeddings;
using OllamaSharp;
using OllamaSharp.Models;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Services;

public sealed class OllamaTextEmbeddingGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OllamaTextEmbeddingGenerationTests()
    {
        this._messageHandlerStub = new();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(File.ReadAllText("TestData/embeddings_test_response.json"));
        this._httpClient = new HttpClient(this._messageHandlerStub, false) { BaseAddress = new Uri("http://localhost:11434") };
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var expectedModel = "fake-model";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsEmbeddingGenerationService();

        //Act
        await sut.GenerateEmbeddingsAsync(["fake-text"]);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<EmbedRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.Equal("fake-text", requestPayload.Input[0]);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var expectedModel = "fake-model";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsEmbeddingGenerationService();

        //Act
        var contents = await sut.GenerateEmbeddingsAsync(["fake-text"]);

        //Assert
        Assert.NotNull(contents);
        Assert.Equal(2, contents.Count);

        var content = contents[0];
        Assert.Equal(5, content.Length);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
