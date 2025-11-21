// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.SemanticKernel.Connectors.VoyageAI;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="VoyageAIContextualizedEmbeddingGenerationService"/>.
/// </summary>
public sealed class VoyageAIContextualizedEmbeddingGenerationServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VoyageAIContextualizedEmbeddingGenerationServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub);
    }

    [Fact]
    public void Constructor_WithValidParameters_CreatesInstance()
    {
        // Arrange & Act
        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        // Assert
        service.Should().NotBeNull();
        service.Attributes.Should().ContainKey("ModelId");
        service.Attributes["ModelId"].Should().Be("voyage-3");
    }

    [Fact]
    public void Constructor_WithNullModelId_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new VoyageAIContextualizedEmbeddingGenerationService(
                modelId: null!,
                apiKey: "test-api-key"
            )
        );
    }

    [Fact]
    public void Constructor_WithNullApiKey_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new VoyageAIContextualizedEmbeddingGenerationService(
                modelId: "voyage-3",
                apiKey: null!
            )
        );
    }

    [Fact]
    public async Task GenerateContextualizedEmbeddingsAsync_ReturnsEmbeddings()
    {
        // Arrange
        var expectedEmbeddings = new List<float[]>
        {
            new[] { 0.1f, 0.2f, 0.3f },
            new[] { 0.4f, 0.5f, 0.6f }
        };

        var responseContent = JsonSerializer.Serialize(new
        {
            results = new[]
            {
                new
                {
                    embeddings = new[]
                    {
                        new { embedding = expectedEmbeddings[0], index = 0 },
                        new { embedding = expectedEmbeddings[1], index = 1 }
                    }
                }
            },
            total_tokens = 20
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var inputs = new List<IList<string>>
        {
            new List<string> { "chunk1", "chunk2" }
        };

        // Act
        var result = await service.GenerateContextualizedEmbeddingsAsync(inputs).ConfigureAwait(false);

        // Assert
        result.Should().NotBeNull();
        result.Should().HaveCount(2);
        result[0].Length.Should().Be(3);
        result[1].Length.Should().Be(3);
    }

    [Fact]
    public async Task GenerateContextualizedEmbeddingsAsync_SendsCorrectRequest()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            results = new[]
            {
                new
                {
                    embeddings = new[]
                    {
                        new { embedding = new[] { 0.1f, 0.2f }, index = 0 }
                    }
                }
            },
            total_tokens = 10
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var inputs = new List<IList<string>>
        {
            new List<string> { "test chunk" }
        };

        // Act
        await service.GenerateContextualizedEmbeddingsAsync(inputs).ConfigureAwait(false);

        // Assert
        this._messageHandlerStub.RequestContent.Should().NotBeNull();
        this._messageHandlerStub.RequestContent.Should().Contain("voyage-3");
        this._messageHandlerStub.RequestContent.Should().Contain("test chunk");
        this._messageHandlerStub.RequestHeaders.Should().ContainKey("Authorization");
    }

    [Fact]
    public async Task GenerateContextualizedEmbeddingsAsync_SendsCorrectModel()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            results = new[]
            {
                new
                {
                    embeddings = new[]
                    {
                        new { embedding = new[] { 0.1f, 0.2f }, index = 0 }
                    }
                }
            },
            total_tokens = 10
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var inputs = new List<IList<string>>
        {
            new List<string> { "test chunk" }
        };

        // Act
        var result = await service.GenerateContextualizedEmbeddingsAsync(inputs).ConfigureAwait(false);

        // Assert
        result.Should().NotBeNull();
        this._messageHandlerStub.RequestContent.Should().NotBeNull();
        this._messageHandlerStub.RequestContent.Should().Contain("voyage-3");
    }

    [Fact]
    public async Task GenerateContextualizedEmbeddingsAsync_HandlesApiError()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
        {
            Content = new StringContent("API error")
        };

        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var inputs = new List<IList<string>>
        {
            new List<string> { "test" }
        };

        // Act & Assert
        await Assert.ThrowsAsync<HttpRequestException>(
            async () => await service.GenerateContextualizedEmbeddingsAsync(inputs).ConfigureAwait(false)
        ).ConfigureAwait(false);
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_WrapsToContextualizedCall()
    {
        // Arrange
        var expectedEmbedding = new[] { 0.1f, 0.2f, 0.3f };

        var responseContent = JsonSerializer.Serialize(new
        {
            results = new[]
            {
                new
                {
                    embeddings = new[]
                    {
                        new { embedding = expectedEmbedding, index = 0 }
                    }
                }
            },
            total_tokens = 10
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var data = new List<string> { "text1" };

        // Act
        var result = await service.GenerateEmbeddingsAsync(data).ConfigureAwait(false);

        // Assert
        result.Should().NotBeNull();
        result.Should().HaveCount(1);
        result[0].Length.Should().Be(3);
    }

    [Fact]
    public void Attributes_ContainsModelId()
    {
        // Arrange & Act
        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        // Assert
        service.Attributes.Should().ContainKey("ModelId");
        service.Attributes["ModelId"].Should().Be("voyage-3");
    }

    [Fact]
    public void ServiceShouldUseCustomEndpoint()
    {
        // Arrange
        var customEndpoint = "https://custom.api.com/v1";

        // Act
        var service = new VoyageAIContextualizedEmbeddingGenerationService(
            modelId: "voyage-3",
            apiKey: "test-api-key",
            endpoint: customEndpoint,
            httpClient: this._httpClient
        );

        // Assert
        service.Should().NotBeNull();
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
