// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.VertexAI;

public sealed class VertexAIHttpRequestFactoryTestsTests
{
    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithAuthorizationHeader()
    {
        // Arrange
        string apiKey = "fake-api-key";
        var sut = new VertexAIHttpRequestFactory(apiKey);
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"Bearer {apiKey}", result.Headers.Authorization!.ToString());
    }

    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithValidMethod()
    {
        // Arrange
        string apiKey = "fake-api-key";
        var sut = new VertexAIHttpRequestFactory(apiKey);
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
        string apiKey = "fake-api-key";
        var sut = new VertexAIHttpRequestFactory(apiKey);
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
        string apiKey = "fake-api-key";
        var sut = new VertexAIHttpRequestFactory(apiKey);
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
        string apiKey = "fake-api-key";
        var sut = new VertexAIHttpRequestFactory(apiKey);
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
