// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextToImage;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextToImageTests"/> class.
/// </summary>
public sealed class AzureOpenAITextToImageTests
{
    /// <summary>
    /// Returns a mocked instance of <see cref="HttpClient"/>.
    /// </summary>
    /// <param name="generationResult">The <see cref="HttpResponseMessage"/> to return for text to image.</param>
    /// <param name="imageResult">The <see cref="HttpResponseMessage"/> to return for image result.</param>
    /// <returns>A mocked <see cref="HttpClient"/> instance.</returns>
    private static HttpClient GetHttpClientMock(HttpResponseMessage generationResult, HttpResponseMessage imageResult)
    {
        var httpClientHandler = new Mock<HttpClientHandler>();

        httpClientHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(request => request.RequestUri!.AbsolutePath.Contains("openai/images/generations:submit")),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(generationResult);

        httpClientHandler
           .Protected()
           .Setup<Task<HttpResponseMessage>>(
               "SendAsync",
               ItExpr.Is<HttpRequestMessage>(request => request.RequestUri!.AbsolutePath.Contains("openai/operations/images")),
               ItExpr.IsAny<CancellationToken>())
           .ReturnsAsync(imageResult);

        return new HttpClient(httpClientHandler.Object);
    }

    /// <summary>
    /// Creates an instance of <see cref="HttpResponseMessage"/> to return with test data.
    /// </summary>
    /// <param name="statusCode">The HTTP status code for the response.</param>
    /// <param name="fileName">The name of the test response file.</param>
    /// <returns>An instance of <see cref="HttpResponseMessage"/> with the specified test data.</returns>
    private static HttpResponseMessage CreateResponseMessage(HttpStatusCode statusCode, string fileName)
    {
        var response = new HttpResponseMessage(statusCode);
        response.Content = new StringContent(OpenAITestHelper.GetTestResponse(fileName), Encoding.UTF8, "application/json");
        return response;
    }

    [Fact]
    public async Task ItShouldGenerateImageSuccussedAsync()
    {
        //Arrange
        using var generateResult = CreateResponseMessage(HttpStatusCode.Accepted, "image_generation_test_response.json");
        using var imageResult = CreateResponseMessage(HttpStatusCode.OK, "image_result_test_response.json");
        using var mockHttpClient = GetHttpClientMock(generateResult, imageResult);

        var generation = new AzureOpenAITextToImageService("https://fake-endpoint/", "gake-model-id", "fake-api-key", mockHttpClient);

        //Act
        var result = await generation.GenerateImageAsync("description", 256, 256);

        //Assert
        Assert.NotNull(result);
    }
}
