// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant;
using Moq;
using System.Threading.Tasks;
using System.Threading;
using Moq.Protected;
using Xunit;
using System;

namespace SemanticKernel.Skills.UnitTests.Memory.Qdrant;

/// <summary>
/// Tests for <see cref="QdrantMemoryStore"/> collection operations.
/// </summary>

public class QdrantMemoryStoreCollectionTests
{
    [Fact]
    public void ConnectionCanBeInitialized()
    {
        // Arrange
        var httpMock = new Mock<HttpClient>();
        var qdrantClient = new QdrantVectorDbClient("http://localhost", 3, 1000, httpMock.Object);
        var db = new QdrantMemoryStore(qdrantClient);
    }

    [Fact]
    public async Task ItCanCreateANewCollectionAsync()
    {
        // Arrange
        var httpMock = new Mock<HttpClient>();
        var qdrantClient = new QdrantVectorDbClient("http://localhost", 3, 1000, httpMock.Object);
        var db = new QdrantMemoryStore(qdrantClient);

        // Act
        await db.CreateCollectionAsync("test");

        // Assert
    }

    private static Mock<HttpMessageHandler> GetHttpMessageHandlerMock(HttpResponseMessage mockResponse)
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(mockResponse);
        return mockHandler;
    }

    private static Mock<HttpMessageHandler> GetHttpMessageHandlerMock(Type exceptionType)
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ThrowsAsync(Activator.CreateInstance(exceptionType) as Exception);
        return mockHandler;
    }
}
