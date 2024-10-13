// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.TextCompletion;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextCompletion"/> class.
/// </summary>
public class HuggingFaceTextCompletionTests : IDisposable
{
    private const string Endpoint = "http://localhost:5000/completions";
    private const string Model = "gpt2";

    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = HttpStatusCode.OK,
    };

    /// <summary>
    /// Verifies that <see cref="HuggingFaceTextCompletion.CompleteAsync(string, JsonObject, CancellationToken)"/>
    /// returns expected completed text without errors.
    /// </summary>
    [Fact]
    public async Task ItReturnsCompletionCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test";
        JsonObject requestSettings = new();

        using var service = this.CreateService(HuggingFaceTestHelper.GetTestResponse("completion_test_response.json"));

        // Act
        var completion = await service.CompleteAsync(Prompt, requestSettings);

        // Assert
        Assert.Equal("This is test completion response", completion);
    }

    /// <summary>
    /// Initializes <see cref="HuggingFaceTextCompletion"/> with mocked <see cref="HttpClientHandler"/>.
    /// </summary>
    /// <param name="testResponse">Test response for <see cref="HttpClientHandler"/> to return.</param>
    private HuggingFaceTextCompletion CreateService(string testResponse)
    {
        this._response.Content = new StringContent(testResponse);

        var httpClientHandler = HuggingFaceTestHelper.GetHttpClientHandlerMock(this._response);

        return new HuggingFaceTextCompletion(new Uri(Endpoint), Model, httpClientHandler);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._response.Dispose();
        }
    }
}
