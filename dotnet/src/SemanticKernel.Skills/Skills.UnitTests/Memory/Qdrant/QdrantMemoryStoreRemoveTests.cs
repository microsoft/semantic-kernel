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
/// Tests for <see cref="QdrantMemoryStore"/> Remove operations.
/// </summary>

public class QdrantMemoryStoreRemoveTests
{
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
