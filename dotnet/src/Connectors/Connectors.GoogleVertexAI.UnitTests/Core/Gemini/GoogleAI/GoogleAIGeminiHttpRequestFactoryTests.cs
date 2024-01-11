#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.GoogleAI;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.GoogleAI;

public sealed class GoogleAIGeminiHttpRequestFactoryTests
{
    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithValidMethod()
    {
        // Arrange
        var sut = new GoogleAIGeminiHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(HttpMethod.Post, result.Method);
    }

    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithValidEndpoint()
    {
        // Arrange
        var sut = new GoogleAIGeminiHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(endpoint, result.RequestUri);
    }

    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithValidUserAgent()
    {
        // Arrange
        var sut = new GoogleAIGeminiHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(HttpHeaderValues.UserAgent, result.Headers.UserAgent.ToString());
    }

    [Fact]
    public async Task CreatePostWhenCalledReturnsHttpRequestMessageWithValidContentAsync()
    {
        // Arrange
        var sut = new GoogleAIGeminiHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        string content = await result.Content!.ReadAsStringAsync();
        Assert.True(JsonNode.DeepEquals(requestData, JsonNode.Parse(content)));
    }
}
