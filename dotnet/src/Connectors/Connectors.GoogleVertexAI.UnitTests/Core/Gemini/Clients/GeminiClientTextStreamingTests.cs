// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.Clients;

public sealed class GeminiClientTextStreamingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/completion_stream_response.json";

    public GeminiClientTextStreamingTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldCallStreamChatCompletionMethodAsync()
    {
        // Arrange
        var mock = GetGeminiChatCompletionMockForChatStream();
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        await sut.StreamGenerateTextAsync("fake-text").ToListAsync();

        // Assert
        mock.VerifyAll();
    }

    [Fact]
    public async Task ShouldReturnValidTextAsync()
    {
        // Arrange
        var streamingChatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatStream(streamingChatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var streamingTextContents = await sut.StreamGenerateTextAsync("fake-text").ToListAsync();

        // Assert
        Assert.Collection(streamingTextContents,
            t => Assert.Equal(streamingChatMessageContents[0].Content, t.Text),
            t => Assert.Equal(streamingChatMessageContents[1].Content, t.Text));
    }

    [Fact]
    public async Task ShouldReturnValidModelIdAsync()
    {
        // Arrange
        var streamingChatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatStream(streamingChatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var streamingTextContents = await sut.StreamGenerateTextAsync("fake-text").ToListAsync();

        // Assert
        Assert.Collection(streamingTextContents,
            t => Assert.Equal(streamingChatMessageContents[0].ModelId, t.ModelId),
            t => Assert.Equal(streamingChatMessageContents[1].ModelId, t.ModelId));
    }

    [Fact]
    public async Task ShouldReturnValidMetadataAsync()
    {
        // Arrange
        var streamingChatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatStream(streamingChatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var streamingTextContents = await sut.StreamGenerateTextAsync("fake-text").ToListAsync();

        // Assert
        Assert.Collection(streamingTextContents,
            t => Assert.Same(streamingChatMessageContents[0].Metadata, t.Metadata),
            t => Assert.Same(streamingChatMessageContents[1].Metadata, t.Metadata));
    }

    [Fact]
    public async Task ShouldReturnValidChoiceIndexAsync()
    {
        // Arrange
        var streamingChatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatStream(streamingChatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var streamingTextContents = await sut.StreamGenerateTextAsync("fake-text").ToListAsync();

        // Assert
        Assert.Collection(streamingTextContents,
            t => Assert.Equal(((GeminiMetadata)streamingChatMessageContents[0].Metadata!).Index, t.ChoiceIndex),
            t => Assert.Equal(((GeminiMetadata)streamingChatMessageContents[1].Metadata!).Index, t.ChoiceIndex));
    }

    private static Mock<IGeminiChatCompletionClient> GetGeminiChatCompletionMockForChatStream(IEnumerable<StreamingChatMessageContent>? streamChatMessageContents = null)
    {
        streamChatMessageContents ??= GetSampleListOfChatMessageContents();

        var mock = new Mock<IGeminiChatCompletionClient>();
        mock.Setup(c => c.StreamGenerateChatMessageAsync(
                It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()))
            .Returns(streamChatMessageContents.ToAsyncEnumerable());

        return mock;
    }

    private static List<StreamingChatMessageContent> GetSampleListOfChatMessageContents()
    {
        var firstChatMessageContent = new StreamingChatMessageContent(
            role: AuthorRole.Assistant,
            content: "test_content",
            modelId: "example-model",
            innerContent: new object(),
            metadata: new GeminiMetadata() { Index = 0 });
        var secondChatMessageContent = new StreamingChatMessageContent(
            role: AuthorRole.Assistant,
            content: "test_content2",
            modelId: "example-model",
            innerContent: new object(),
            metadata: new GeminiMetadata() { Index = 1 });
        List<StreamingChatMessageContent> chatMessageContents = [firstChatMessageContent, secondChatMessageContent];
        return chatMessageContents;
    }

    private static GeminiTextGenerationClient CreateTextGenerationClient(
        IGeminiChatCompletionClient chatCompletionClient)
    {
        return new GeminiTextGenerationClient(chatCompletionClient);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
