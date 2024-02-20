// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.GoogleAI;

public sealed class GoogleAIHttpRequestFactoryTests
{
    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithValidMethod()
    {
        // Arrange
        var sut = new GoogleAIHttpRequestFactory();
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
        var sut = new GoogleAIHttpRequestFactory();
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
        var sut = new GoogleAIHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, result.Headers.UserAgent.ToString());
    }

    [Fact]
    public void CreatePostWhenCalledReturnsHttpRequestMessageWithSemanticKernelVersionHeader()
    {
        // Arrange
        var sut = new GoogleAIHttpRequestFactory();
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(GoogleAIHttpRequestFactory));

        // Act
        var request = sut.CreatePost(requestData, endpoint);

        // Assert
        var header = request.Headers.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Fact]
    public async Task CreatePostWhenCalledReturnsHttpRequestMessageWithValidContentAsync()
    {
        // Arrange
        var sut = new GoogleAIHttpRequestFactory();
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
