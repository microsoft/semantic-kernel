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
using Moq;
using Moq.Protected;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="VoyageAITextEmbeddingGenerationService"/>.
/// </summary>
public sealed class VoyageAITextEmbeddingGenerationServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VoyageAITextEmbeddingGenerationServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub);
    }

    [Fact]
    public void ConstructorShouldInitializeService()
    {
        // Arrange & Act
        var service = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        // Assert
        service.Should().NotBeNull();
        service.Attributes.Should().ContainKey("ModelId");
    }

    [Fact]
    public void ConstructorShouldThrowWhenModelIdIsNull()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new VoyageAITextEmbeddingGenerationService(
                modelId: null!,
                apiKey: "test-api-key"
            )
        );
    }

    [Fact]
    public void ConstructorShouldThrowWhenApiKeyIsNull()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new VoyageAITextEmbeddingGenerationService(
                modelId: "voyage-3-large",
                apiKey: null!
            )
        );
    }

    [Fact]
    public async Task GenerateEmbeddingsAsyncShouldReturnEmbeddings()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            data = new[]
            {
                new { embedding = new[] { 0.1f, 0.2f, 0.3f }, index = 0, @object = "embedding" },
                new { embedding = new[] { 0.4f, 0.5f, 0.6f }, index = 1, @object = "embedding" }
            },
            usage = new { total_tokens = 10 }
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var data = new List<string> { "text1", "text2" };

        // Act
        var result = await service.GenerateEmbeddingsAsync(data).ConfigureAwait(false);

        // Assert
        result.Should().NotBeNull();
        result.Should().HaveCount(2);
        result[0].Length.Should().Be(3);
        result[1].Length.Should().Be(3);
    }

    [Fact]
    public async Task GenerateEmbeddingsAsyncShouldSendCorrectRequest()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new
        {
            data = new[]
            {
                new { embedding = new[] { 0.1f, 0.2f }, index = 0, @object = "embedding" }
            },
            usage = new { total_tokens = 5 }
        });

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent)
        };

        var service = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var data = new List<string> { "test text" };

        // Act
        await service.GenerateEmbeddingsAsync(data).ConfigureAwait(false);

        // Assert
        this._messageHandlerStub.RequestContent.Should().NotBeNull();
        this._messageHandlerStub.RequestContent.Should().Contain("voyage-3-large");
        this._messageHandlerStub.RequestContent.Should().Contain("test text");
        this._messageHandlerStub.RequestHeaders.Should().ContainKey("Authorization");
    }

    [Fact]
    public async Task GenerateEmbeddingsAsyncShouldHandleApiError()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
        {
            Content = new StringContent("API error")
        };

        var service = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
            apiKey: "test-api-key",
            httpClient: this._httpClient
        );

        var data = new List<string> { "test" };

        // Act & Assert
        await Assert.ThrowsAsync<HttpRequestException>(
            async () => await service.GenerateEmbeddingsAsync(data).ConfigureAwait(false)
        ).ConfigureAwait(false);
    }

    [Fact]
    public void ServiceShouldUseCustomEndpoint()
    {
        // Arrange
        var customEndpoint = "https://custom.api.com/v1";

        // Act
        var service = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
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
