#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Core.VertexAI;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core.VertexAI;

public sealed class VertexAIGeminiHttpRequestFactoryTestsTests
{
    [Fact]
    public async Task CreateWhenCalledReturnsValidHttpRequestMessageAsync()
    {
        // Arrange
        string apiKey = "fake-api-key";
        var sut = new VertexAIGeminiHttpRequestFactory(apiKey);
        var requestData = JsonNode.Parse("""{"text":"Hello world!"}""")!;
        var endpoint = new Uri("https://example.com");

        // Act
        var result = sut.CreatePost(requestData, endpoint);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(HttpMethod.Post, result.Method);
        Assert.Equal(endpoint, result.RequestUri);
        Assert.Equal(HttpHeaderValues.UserAgent, result.Headers.UserAgent.ToString());
        Assert.Equal($"Bearer {apiKey}", result.Headers.Authorization!.ToString());
        string content = await result.Content!.ReadAsStringAsync();
        Assert.True(JsonNode.DeepEquals(requestData, JsonNode.Parse(content)));
    }
}
