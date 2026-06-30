// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextGenerationService"/> class.
/// </summary>
public sealed class HuggingFaceTextGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("textgeneration_test_response.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", apiKey: null, httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", apiKey: "fake-api-key", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("Authorization");

        var value = values.SingleOrDefault();
        Assert.Equal("Bearer fake-api-key", value);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

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
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://router.huggingface.co/hf-inference/models", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/models/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextGenerationRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal("fake-text", requestPayload.Inputs);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync("fake-test");

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);

        Assert.Equal("Write about the difference between Data Science and AI Engineering.\n\nData Science and AI Engineering are two interconnected fields that have gained immense popularity in recent years. While both fields deal with data and machine learning, they have distinct differences in terms of their focus, skills required, and applications.\n\nData Science is a multidisciplinary field that involves the extraction of insights and knowledge from large and complex data sets. It combines various disciplines such as mathematics, statistics, computer science, and domain expertise to analyze and interpret data. Data scientists use a variety of tools and techniques such as data cleaning, data wrangling, data visualization, and machine learning algorithms to derive insights and make informed decisions. They work closely with stakeholders to understand business requirements and translate them into data", content.Text);
    }

    [Fact]
    public async Task ShouldHandleMetadataAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync("fake-test");

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);

        Assert.NotNull(content.Metadata);
        Assert.IsType<HuggingFaceTextGenerationMetadata>(content.Metadata);

        var metadata = content.Metadata as HuggingFaceTextGenerationMetadata;

        var prefillTokens = JsonElement.Parse(JsonSerializer.Serialize(metadata!.PrefillTokens));
        var tokens = JsonElement.Parse(JsonSerializer.Serialize(metadata.Tokens));

        Assert.Equal("length", metadata!.FinishReason);
        Assert.Equal(150, metadata.GeneratedTokens);
        Assert.Equal(0, prefillTokens.GetArrayLength());
        Assert.Equal(150, tokens.GetArrayLength());

        Assert.Equal("Write about the difference between Data Science and AI Engineering.\n\nData Science and AI Engineering are two interconnected fields that have gained immense popularity in recent years. While both fields deal with data and machine learning, they have distinct differences in terms of their focus, skills required, and applications.\n\nData Science is a multidisciplinary field that involves the extraction of insights and knowledge from large and complex data sets. It combines various disciplines such as mathematics, statistics, computer science, and domain expertise to analyze and interpret data. Data scientists use a variety of tools and techniques such as data cleaning, data wrangling, data visualization, and machine learning algorithms to derive insights and make informed decisions. They work closely with stakeholders to understand business requirements and translate them into data", content.Text);
    }

    [Fact]
    public async Task GetTextContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync("fake-test");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("""
                [
                    {
                        "generated_text": "Why the sky is blue? | Dept. of Science & Mathematics Education | University of Notre Dame\nWhen I was in high school I had a pretty simple conception of reality. I believed that if something made sense to me, then it must also be true. I believed that some problems were so fundamental that I couldn’t understand"
                    }
                ]
                """, Encoding.UTF8, "application/json")
        };

        // Act
        var textContent = await sut.GetTextContentAsync("Any prompt");

        // Assert
        Assert.NotNull(textContent.ModelId);
        Assert.Equal("fake-model", textContent.ModelId);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
