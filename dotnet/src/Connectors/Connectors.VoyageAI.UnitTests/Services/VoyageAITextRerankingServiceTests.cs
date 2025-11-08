// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.SemanticKernel.Connectors.VoyageAI;
using Microsoft.SemanticKernel.Reranking;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="VoyageAITextRerankingService"/>.
/// </summary>
public sealed class VoyageAITextRerankingServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VoyageAITextRerankingServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub);
    }

    [Fact]
    public void ConstructorShouldInitializeService()
    {
        // Arrange & Act
        var service = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        // Assert
        service.Should().NotBeNull();
        service.Attributes.Should().ContainKey("ModelId");
    }

    [Fact]
    public async Task RerankAsyncShouldReturnRankedResults()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            data = new[]
            {
                new { index = 2, relevance_score = 0.95 },
                new { index = 0, relevance_score = 0.75 },
                new { index = 1, relevance_score = 0.50 }
            },
            usage = new { total_tokens = 20 }
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var query = "test query";
        var documents = new List<string> { "doc1", "doc2", "doc3" };

        // Act
        var results = await service.RerankAsync(query, documents).ConfigureAwait(false);

        // Assert
        results.Should().NotBeNull();
        results.Should().HaveCount(3);
        results[0].Index.Should().Be(2);
        results[0].RelevanceScore.Should().Be(0.95);
        results[1].Index.Should().Be(0);
        results[1].RelevanceScore.Should().Be(0.75);
    }

    [Fact]
    public async Task RerankAsyncShouldSendCorrectRequest()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            data = new[] { new { index = 0, relevance_score = 0.5 } },
            usage = new { total_tokens = 5 }
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var query = "What is SK?";
        var documents = new List<string> { "Semantic Kernel is an SDK" };

        // Act
        await service.RerankAsync(query, documents).ConfigureAwait(false);

        // Assert
        this._messageHandlerStub.RequestContent.Should().NotBeNull();
        this._messageHandlerStub.RequestContent.Should().Contain("What is SK?");
        this._messageHandlerStub.RequestContent.Should().Contain("rerank-2.5");
        this._messageHandlerStub.RequestHeaders.Should().ContainKey("Authorization");
    }

    [Fact]
    public async Task RerankAsyncShouldHandleEmptyResults()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            data = Array.Empty<object>(),
            usage = new { total_tokens = 0 }
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var query = "test";
        var documents = new List<string> { "doc" };

        // Act
        var results = await service.RerankAsync(query, documents).ConfigureAwait(false);

        // Assert
        results.Should().NotBeNull();
        results.Should().BeEmpty();
    }

    [Fact]
    public async Task RerankAsyncShouldHandleApiError()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.InternalServerError)
        {
            Content = new StringContent("API error")
        };

        var service = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var query = "test";
        var documents = new List<string> { "doc" };

        // Act & Assert
        await Assert.ThrowsAsync<HttpRequestException>(
            async () => await service.RerankAsync(query, documents).ConfigureAwait(false)
        ).ConfigureAwait(false);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private sealed class HttpMessageHandlerStub : HttpMessageHandler
    {
        public HttpResponseMessage? ResponseToReturn { get; set; }
        public string? RequestContent { get; private set; }
        public Dictionary<string, string> RequestHeaders { get; } = new();

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            if (request.Content is not null)
            {
                this.RequestContent = await request.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            }

            foreach (var header in request.Headers)
            {
                this.RequestHeaders[header.Key] = string.Join(",", header.Value);
            }

            return this.ResponseToReturn ?? new HttpResponseMessage(HttpStatusCode.OK);
        }
    }
}
