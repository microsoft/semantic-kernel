// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini.Clients;

public sealed class GeminiCountingTokensTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/counttokens_response.json";

    public GeminiCountingTokensTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldContainModelInRequestUriAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateTokenCounterClient(modelId: modelId);

        // Act
        await client.CountTokensAsync("fake-text");

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.Contains(modelId, this._messageHandlerStub.RequestUri.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldReturnGreaterThanZeroTokenCountAsync()
    {
        // Arrange
        var client = this.CreateTokenCounterClient();

        // Act
        var tokenCount = await client.CountTokensAsync("fake-text");

        // Assert
        Assert.True(tokenCount > 0);
    }

    [Fact]
    public async Task ItCreatesPostRequestIfBearerIsSpecifiedWithAuthorizationHeaderAsync()
    {
        // Arrange
        string bearerKey = "fake-key";
        var client = this.CreateTokenCounterClient(bearerKey: bearerKey);

        // Act
        await client.CountTokensAsync("fake-text");

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.NotNull(this._messageHandlerStub.RequestHeaders.Authorization);
        Assert.Equal($"Bearer {bearerKey}", this._messageHandlerStub.RequestHeaders.Authorization.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateTokenCounterClient();

        // Act
        await client.CountTokensAsync("fake-text");

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateTokenCounterClient();

        // Act
        await client.CountTokensAsync("fake-text");

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateTokenCounterClient();
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientBase));

        // Act
        await client.CountTokensAsync("fake-text");

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Theory]
    [InlineData("https://malicious-site.com")]
    [InlineData("http://internal-network.local")]
    [InlineData("ftp://attacker.com")]
    [InlineData("//bypass.com")]
    [InlineData("javascript:alert(1)")]
    [InlineData("data:text/html,<script>alert(1)</script>")]
    public void ItThrowsOnLocationUrlInjectionAttempt(string maliciousLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
        {
            var client = new GeminiTokenCounterClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: maliciousLocation,
                projectId: "fake-project-id");
        });
    }

    [Theory]
    [InlineData("useast1")]
    [InlineData("us-east1")]
    [InlineData("europe-west4")]
    [InlineData("asia-northeast1")]
    [InlineData("us-central1-a")]
    [InlineData("northamerica-northeast1")]
    [InlineData("australia-southeast1")]
    public void ItAcceptsValidHostnameSegments(string validLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        var exception = Record.Exception(() =>
        {
            var client = new GeminiTokenCounterClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: validLocation,
                projectId: "fake-project-id");
        });

        Assert.Null(exception);
    }

    private sealed class BearerTokenGenerator()
    {
        private int _index = 0;
        public required List<string> BearerKeys { get; init; }

        public ValueTask<string> GetBearerToken() => ValueTask.FromResult(this.BearerKeys[this._index++]);
    }

    private GeminiTokenCounterClient CreateTokenCounterClient(
        string modelId = "fake-model",
        string? bearerKey = null)
    {
        if (bearerKey is not null)
        {
            return new GeminiTokenCounterClient(
                httpClient: this._httpClient,
                modelId: modelId,
                bearerTokenProvider: () => ValueTask.FromResult(bearerKey),
                apiVersion: VertexAIVersion.V1,
                location: "fake-location",
                projectId: "fake-project-id");
        }

        return new GeminiTokenCounterClient(
            httpClient: this._httpClient,
            modelId: modelId,
            apiVersion: GoogleAIVersion.V1,
            apiKey: "fake-key");
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
