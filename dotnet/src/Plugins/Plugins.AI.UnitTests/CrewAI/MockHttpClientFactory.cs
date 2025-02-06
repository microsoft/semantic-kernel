// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Moq;

namespace SemanticKernel.Plugins.AI.UnitTests.CrewAI;

/// <summary>
/// Implementation of <see cref="IHttpClientFactory"/> which uses the <see cref="MultipleHttpMessageHandlerStub"/>.
/// </summary>
internal sealed class MockHttpClientFactory(Mock<HttpMessageHandler> mockHandler) : IHttpClientFactory, IDisposable
{
    public HttpClient CreateClient(string name)
    {
        return new(mockHandler.Object);
    }

    public void Dispose()
    {
        mockHandler.Object.Dispose();
        GC.SuppressFinalize(this);
    }
}
