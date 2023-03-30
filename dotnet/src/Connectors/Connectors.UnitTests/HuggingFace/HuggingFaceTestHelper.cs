// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Moq;
using Moq.Protected;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace;

/// <summary>
/// Helper for HuggingFace test purposes.
/// </summary>
internal static class HuggingFaceTestHelper
{
    /// <summary>
    /// Reads test response from file for mocking purposes.
    /// </summary>
    /// <param name="fileName">Name of the file with test response.</param>
    internal static string GetTestResponse(string fileName)
    {
        return File.ReadAllText($"./HuggingFace/TestData/{fileName}");
    }

    /// <summary>
    /// Returns mocked instance of <see cref="HttpClientHandler"/>.
    /// </summary>
    /// <param name="httpResponseMessage">Message to return for mocked <see cref="HttpClientHandler"/>.</param>
    internal static HttpClientHandler GetHttpClientHandlerMock(HttpResponseMessage httpResponseMessage)
    {
        var httpClientHandler = new Mock<HttpClientHandler>();

        httpClientHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(httpResponseMessage);

        return httpClientHandler.Object;
    }
}
