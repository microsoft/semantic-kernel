// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp.Models;
using OllamaSharp.Models.Chat;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Services;

public sealed class OllamaTextGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OllamaTextGenerationTests()
    {
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/text_generation_test_response_stream.txt"))
            }
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false) { BaseAddress = new Uri("http://localhost:11434") };
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        var sut = new OllamaTextGenerationService(
            expectedModel,
            httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        var requestPayload = JsonSerializer.Deserialize<GenerateRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.Equal("fake-text", requestPayload.Prompt);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync("fake-test");

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);
        Assert.Equal("This is test completion response", content.Text);
    }

    [Fact]
    public async Task GetTextContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        var sut = new OllamaTextGenerationService(
            expectedModel,
            httpClient: this._httpClient);

        // Act
        var textContent = await sut.GetTextContentAsync("Any prompt");

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        Assert.NotNull(textContent.ModelId);
        Assert.Equal(expectedModel, textContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        var sut = new OllamaTextGenerationService(
            expectedModel,
            httpClient: this._httpClient);

        // Act
        StreamingTextContent? lastTextContent = null;
        await foreach (var textContent in sut.GetStreamingTextContentsAsync("Any prompt"))
        {
            lastTextContent = textContent;
        }

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        Assert.NotNull(lastTextContent!.ModelId);
        Assert.Equal(expectedModel, lastTextContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsExecutionSettingsMustBeSentAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            httpClient: this._httpClient);

        string jsonSettings = """
                                {
                                    "stop": ["stop me"],
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Act
        await sut.GetStreamingTextContentsAsync("Any prompt", ollamaExecutionSettings).GetAsyncEnumerator().MoveNextAsync();

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Equal(ollamaExecutionSettings.Stop, requestPayload.Options.Stop);
        Assert.Equal(ollamaExecutionSettings.Temperature, requestPayload.Options.Temperature);
        Assert.Equal(ollamaExecutionSettings.TopP, requestPayload.Options.TopP);
        Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
    }

    [Fact]
    public async Task GetTextContentsExecutionSettingsMustBeSentAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            httpClient: this._httpClient);
        string jsonSettings = """
                                {
                                    "stop": ["stop me"],
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Act
        await sut.GetTextContentsAsync("Any prompt", ollamaExecutionSettings);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Equal(ollamaExecutionSettings.Stop, requestPayload.Options.Stop);
        Assert.Equal(ollamaExecutionSettings.Temperature, requestPayload.Options.Temperature);
        Assert.Equal(ollamaExecutionSettings.TopP, requestPayload.Options.TopP);
        Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
    }

    /// <summary>
    /// Disposes resources used by this class.
    /// </summary>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();

        this._httpClient.Dispose();
    }
}
