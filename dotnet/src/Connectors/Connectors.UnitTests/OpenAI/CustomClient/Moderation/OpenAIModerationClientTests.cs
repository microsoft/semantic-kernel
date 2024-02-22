// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.CustomClient.Moderation;

[SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "Test code")]
public sealed class OpenAIModerationClientTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./OpenAI/TestData/moderation_response.json";

    public OpenAIModerationClientTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content =
            new StringContent(File.ReadAllText(TestDataFilePath));
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void ConstructorWhenModelIdIsNullOrWhiteSpaceThrowsArgumentException(string? modelId)
    {
        // Act and Assert
        Assert.ThrowsAny<ArgumentException>(() => this.CreateOpenAIModerationClient(modelId: modelId!));
    }

    [Fact]
    public async Task ItCreatesRequestUsingHttpRequestFactoryAsync()
    {
        // Arrange
        var httpRequestFactoryMock = new Mock<IHttpRequestFactory>();
        httpRequestFactoryMock
            .Setup(f => f.CreatePost(It.IsAny<object>(), It.IsAny<Uri>()))
            .Returns(new HttpRequestMessage(HttpMethod.Post, new Uri("https://example.com/")));
        var sut = this.CreateOpenAIModerationClient(httpRequestFactory: httpRequestFactoryMock.Object);

        // Act
        await sut.ClassifyTextsAsync(["text", "text2", "text3"]);

        // Assert
        httpRequestFactoryMock.VerifyAll();
    }

    [Fact]
    public async Task WhenTextsCollectionIsNullThrowsArgumentNullExceptionAsync()
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();

        // Act and Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() => sut.ClassifyTextsAsync(null!));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public async Task WhenTextsValuesAreNullOrWhiteSpaceThrowsArgumentExceptionAsync(string? text)
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();

        // Act and Assert
        await Assert.ThrowsAsync<ArgumentException>(() => sut.ClassifyTextsAsync([text]));
    }

    [Fact]
    public async Task ItSendsRequestWithModelIdInBodyAsync()
    {
        // Arrange
        string modelId = "sample-model";
        var sut = this.CreateOpenAIModerationClient(modelId: modelId);

        // Act
        await sut.ClassifyTextsAsync(["text", "text2", "text3"]);

        // Assert
        var request = this.DeserializeRequestContent();
        Assert.NotNull(request);
        Assert.Equal(modelId, request.Model);
    }

    [Fact]
    public async Task ItSendRequestWithTextsInBodyAsync()
    {
        // Arrange
        List<string> texts = ["text", "text2", "text3"];
        var sut = this.CreateOpenAIModerationClient();

        // Act
        await sut.ClassifyTextsAsync(texts);

        // Assert
        var request = this.DeserializeRequestContent();
        Assert.NotNull(request);
        Assert.Equal(texts, request.Input);
    }

    [Fact]
    public async Task ItReturnsClassificationContentWithModelIdFromResponseAsync()
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();

        // Act
        var result = await sut.ClassifyTextsAsync(["text", "text2", "text3"]);

        // Assert
        var sampleResponse = await DeserializeSampleResponseAsync();
        Assert.NotNull(result);
        Assert.All(result, r => Assert.Equal(sampleResponse!.ModelId, r.ModelId));
    }

    [Fact]
    public async Task ItReturnsClassificationContentWithMetadataFromResponseAsync()
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();

        // Act
        var result = await sut.ClassifyTextsAsync(["text", "text2", "text3"]);

        // Assert
        var sampleResponse = await DeserializeSampleResponseAsync();
        Assert.NotNull(result);
        Assert.All(result, r => Assert.Equal(sampleResponse!.Id, r.Metadata!["Id"]));
    }

    [Fact]
    public async Task ItReturnsClassificationContentWithEntriesFromResponseAsync()
    {
        // Arrange
        var sut = this.CreateOpenAIModerationClient();
        List<string> inputs = ["text", "text2", "text3"];

        // Act
        var results = await sut.ClassifyTextsAsync(inputs);

        // Assert
        var sampleResponse = await DeserializeSampleResponseAsync();
        Assert.NotNull(results);
        Assert.All(results, (c, i) =>
        {
            var openAIResult = c.Result as OpenAIClassificationResult;
            Assert.NotNull(openAIResult);
            Assert.Equal(inputs[i], results[i].ClassifiedContent);
            Assert.Equal(sampleResponse!.Results[i].Flagged, openAIResult.Flagged);
            Assert.Equivalent(sampleResponse.Results[i].CategoryFlags,
                openAIResult.Entries.Select(entry => KeyValuePair.Create(entry.Category.Label, entry.Flagged)));
            Assert.Equivalent(sampleResponse.Results[i].CategoryScores,
                openAIResult.Entries.Select(entry => KeyValuePair.Create(entry.Category.Label, entry.Score)));
        });
    }

    private OpenAIModerationClient CreateOpenAIModerationClient(
        HttpClient? httpClient = null,
        string modelId = "modelId",
        IHttpRequestFactory? httpRequestFactory = null,
        ILogger? logger = null)
    {
        return new OpenAIModerationClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory ?? new FakeHttpRequestFactory(),
            logger: logger);
    }

    private static async Task<OpenAIModerationResponse?> DeserializeSampleResponseAsync()
        => JsonSerializer.Deserialize<OpenAIModerationResponse>(await File.ReadAllTextAsync(TestDataFilePath));

    private OpenAIModerationRequest? DeserializeRequestContent()
        => JsonSerializer.Deserialize<OpenAIModerationRequest>(this._messageHandlerStub.RequestContent);

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
