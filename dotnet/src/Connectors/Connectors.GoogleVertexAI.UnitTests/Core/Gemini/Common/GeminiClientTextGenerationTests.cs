// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.Common;

public sealed class GeminiClientTextGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/completion_one_response.json";

    public GeminiClientTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldCallGenerateChatCompletionMethodAsync()
    {
        // Arrange
        var mock = GetGeminiChatCompletionMockForChatGenerate();
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        await sut.GenerateTextAsync("fake-text");

        // Assert
        mock.VerifyAll();
    }

    [Fact]
    public async Task ShouldReturnValidTextAsync()
    {
        // Arrange
        var chatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatGenerate(chatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var textContents = await sut.GenerateTextAsync("fake-text");

        // Assert
        Assert.Collection(textContents,
            t => Assert.Equal(chatMessageContents[0].Content, t.Text),
            t => Assert.Equal(chatMessageContents[1].Content, t.Text));
    }

    [Fact]
    public async Task ShouldReturnValidModelIdAsync()
    {
        // Arrange
        var chatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatGenerate(chatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var textContents = await sut.GenerateTextAsync("fake-text");

        // Assert
        Assert.Collection(textContents,
            t => Assert.Equal(chatMessageContents[0].ModelId, t.ModelId),
            t => Assert.Equal(chatMessageContents[1].ModelId, t.ModelId));
    }

    [Fact]
    public async Task ShouldReturnValidMetadataAsync()
    {
        // Arrange
        var chatMessageContents = GetSampleListOfChatMessageContents();
        var mock = GetGeminiChatCompletionMockForChatGenerate(chatMessageContents);
        var sut = CreateTextGenerationClient(mock.Object);

        // Act
        var textContents = await sut.GenerateTextAsync("fake-text");

        // Assert
        Assert.Collection(textContents,
            t => Assert.Same(chatMessageContents[0].Metadata, t.Metadata),
            t => Assert.Same(chatMessageContents[1].Metadata, t.Metadata));
    }

    private static Mock<IGeminiChatCompletionClient> GetGeminiChatCompletionMockForChatGenerate(List<ChatMessageContent>? chatMessageContents = null)
    {
        chatMessageContents ??= GetSampleListOfChatMessageContents();

        var mock = new Mock<IGeminiChatCompletionClient>();
        mock.Setup(c => c.GenerateChatMessageAsync(
                It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(chatMessageContents);

        return mock;
    }

    private static List<ChatMessageContent> GetSampleListOfChatMessageContents()
    {
        var firstChatMessageContent = new ChatMessageContent(
            role: AuthorRole.Assistant,
            content: "test_content",
            modelId: "example-model",
            innerContent: new object(),
            metadata: new GeminiMetadata());
        var secondChatMessageContent = new ChatMessageContent(
            role: AuthorRole.Assistant,
            content: "test_content2",
            modelId: "example-model",
            innerContent: new object(),
            metadata: new GeminiMetadata());
        List<ChatMessageContent> chatMessageContents = [firstChatMessageContent, secondChatMessageContent];
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
