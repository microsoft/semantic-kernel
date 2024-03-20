// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests;

public sealed class OllamaTextGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OllamaTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(OllamaTestHelper.GetTestResponse("text_generation_test_response.json"));
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");
        var value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        var requestPayload = JsonSerializer.Deserialize<OllamaTextRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.Equal("fake-text", requestPayload.Prompt);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            new Uri("http://localhost:11434"),
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
        var sut = new OllamaTextGenerationService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"
            {
              ""response"": ""This is test completion response"",
              ""model"": ""fake-model""
            }",
                Encoding.UTF8,
                "application/json")
        };

        // Act
        var textContent = await sut.GetTextContentAsync("Any prompt");

        // Assert
        Assert.NotNull(textContent.ModelId);
        Assert.Equal("fake-model", textContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var sut = new OllamaTextGenerationService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"
            {
              ""response"": ""This is test completion response"",
              ""model"": ""fake-model""
            }",
                Encoding.UTF8,
                "application/json")
        };

        // Act
        StreamingTextContent? lastTextContent = null;
        await foreach (var textContent in sut.GetStreamingTextContentsAsync("Any prompt"))
        {
            lastTextContent = textContent;
        }

        // Assert
        Assert.NotNull(lastTextContent!.ModelId);
        Assert.Equal("fake-model", lastTextContent.ModelId);
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
