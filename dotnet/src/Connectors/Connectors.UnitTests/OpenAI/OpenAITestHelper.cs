// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Moq;
using Moq.Protected;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Helper for OpenAI test purposes.
/// </summary>
internal static class OpenAITestHelper
{
    /// <summary>
    /// Reads test response from file for mocking purposes.
    /// </summary>
    /// <param name="fileName">Name of the file with test response.</param>
    internal static string GetTestResponse(string fileName)
    {
        return File.ReadAllText($"./OpenAI/TestData/{fileName}");
    }

    /// <summary>
    /// Creates an instance of <see cref="HttpClientHandler"/> to return with test data.
    /// </summary>
    internal static Mock<HttpClientHandler> StartMockHttpClient()
    {
        return new Mock<HttpClientHandler>();
    }

    /// <summary>
    /// Setup the mock handler to return the specified response message.
    /// </summary>
    /// <param name="mockHandler"> The mock handler to setup.</param>
    /// <param name="url"> The URL to match.</param>
    /// <param name="statusCode">The HTTP status code for the response.</param>
    /// <param name="fileName">The name of the test response file.</param>
    internal static Mock<HttpClientHandler> SetupResponse(this Mock<HttpClientHandler> mockHandler, string url, HttpStatusCode statusCode, string fileName)
    {
        mockHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(request => request.RequestUri!.AbsolutePath.Contains(url)),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(() => new HttpResponseMessage(statusCode)
            {
                Content = new StringContent(GetTestResponse(fileName), Encoding.UTF8, "application/json")
            });

        return mockHandler;
    }

    /// <summary>
    /// Build HttpClient using mock handler.
    /// </summary>
    /// <param name="mockHandler">The mock handler to use.</param>
    /// <returns>Mock HttpClient</returns>
    internal static HttpClient BuildClient(this Mock<HttpClientHandler> mockHandler)
    {
        return new HttpClient(mockHandler.Object);
    }
}
