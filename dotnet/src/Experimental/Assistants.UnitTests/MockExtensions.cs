// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using Moq;
using Moq.Protected;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

internal static class MockExtensions
{
    public static void VerifyMock(this Mock<HttpMessageHandler> mockHandler, HttpMethod method, int times, string? uri = null)
    {
        mockHandler.Protected().Verify(
            "SendAsync",
            Times.Exactly(times),
            ItExpr.Is<HttpRequestMessage>(req => req.Method == method && (uri == null || req.RequestUri == new Uri(uri))),
            ItExpr.IsAny<CancellationToken>());
    }
}
