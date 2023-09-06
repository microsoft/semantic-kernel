// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Moq;
using Moq.Protected;

namespace SemanticKernel.Skills.UnitTests.OpenAPI;

/// <summary>
/// Contains helper methods for OpenApi related tests.
/// </summary>
internal static class OpenApiTestHelper
{
    /// <summary>
    /// Modifies OpenApi document for testing different scenarios.
    /// </summary>
    /// <param name="openApiDocument">The OpenApi document content.</param>
    /// <param name="transformer">Delegate with document modifications.</param>
    internal static MemoryStream ModifyOpenApiDocument(Stream openApiDocument, Action<JsonObject> transformer)
    {
        var json = JsonSerializer.Deserialize<JsonObject>(openApiDocument);

        transformer(json!);

        var stream = new MemoryStream();

        JsonSerializer.Serialize(stream, json);

        stream.Seek(0, SeekOrigin.Begin);

        return stream;
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
