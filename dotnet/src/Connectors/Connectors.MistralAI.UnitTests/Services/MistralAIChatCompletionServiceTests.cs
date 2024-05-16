// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="MistralAIChatCompletionService"/>.
/// </summary>
public sealed class MistralAIChatCompletionServiceTests : MistralTestBase
{
    [Fact]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestData("chat_completions_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var service = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, default);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var service = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = service.GetStreamingChatMessageContentsAsync(chatHistory, default);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        };

        // Assert
        Assert.NotNull(response);
        Assert.Equal(124, chunks.Count);
        foreach (var chunk in chunks)
        {
            Assert.NotNull(chunk);
            Assert.Equal("mistral-small-latest", chunk.ModelId);
            Assert.NotNull(chunk.Content);
            Assert.NotNull(chunk.Role);
            Assert.NotNull(chunk.Metadata);
        }
    }
}
