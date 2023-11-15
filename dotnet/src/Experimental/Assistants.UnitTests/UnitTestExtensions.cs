// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using Moq.Protected;
using Moq;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

internal static class UnitTestExtensions
{
    public static void VerifyMock(this Mock<HttpMessageHandler> mockHandler, HttpMethod method, Uri uri, int times)
    {
        mockHandler.Protected().Verify(
            "SendAsync",
            Times.Exactly(1), // We expectt a single request
            ItExpr.Is<HttpRequestMessage>(req =>
                    req.Method == method
                    && req.RequestUri == uri
            ),
            ItExpr.IsAny<CancellationToken>()
        );
    }

    public static void VerifyMock(this Mock<HttpMessageHandler> mockHandler, HttpMethod method, string uri, int times)
    {
        mockHandler.VerifyMock(method, new Uri(uri), times);
    }
}
