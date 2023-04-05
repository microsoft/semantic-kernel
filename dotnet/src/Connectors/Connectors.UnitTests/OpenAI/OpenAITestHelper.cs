// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Linq.Expressions;
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
    /// Returns mocked instance of <see cref="DelegatingHandler"/>.
    /// </summary>
    /// <param name="httpResponseMessage">Message to return for mocked <see cref="DelegatingHandler"/>.</param>
    internal static DelegatingHandler GetAzureDelegatingHandlerMock(HttpResponseMessage httpResponseMessage)
    {
        var delegatingHandler = new Mock<DelegatingHandler>();

        delegatingHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(httpResponseMessage);

        // Azure Completion will cache the model list by requesting the Deployment API.
        delegatingHandler
          .Protected()
          .Setup<Task<HttpResponseMessage>>(
              "SendAsync",
              ItExpr.Is<HttpRequestMessage>(request => request.RequestUri != null && request.RequestUri.LocalPath == "/openai/deployments"),
              ItExpr.IsAny<CancellationToken>())
          .ReturnsAsync(() => new HttpResponseMessage()
          {
              Content = new StringContent(GetTestResponse("deployment_test_response.json"))
          });

        return delegatingHandler.Object;
    }



    /// <summary>
    /// Returns mocked instance of <see cref="MockDelegatingHandlerFactory"/>.
    /// </summary>
    /// <param name="httpResponseMessage">Message to return for mocked <see cref="MockDelegatingHandlerFactory"/>.</param>
    internal static MockDelegatingHandlerFactory GetAzureDelegatingHandlerFactoryMock(HttpResponseMessage httpResponseMessage)
    {
        return new MockDelegatingHandlerFactory(GetAzureDelegatingHandlerMock(httpResponseMessage));
    }
}
