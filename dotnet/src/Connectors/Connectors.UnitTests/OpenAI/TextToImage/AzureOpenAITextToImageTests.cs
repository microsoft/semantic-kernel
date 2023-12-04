// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextToImage;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextToImage;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextToImageServiceTests"/> class.
/// </summary>
public sealed class AzureOpenAITextToImageServiceTests
{
    [Fact]
    public void ItValidatesTheModelId()
    {
        // Arrange
        const string InvalidModel = "dall-e-3";

        const string ValidModel1 = "dall-e-2";
        const string ValidModel2 = "Dall-E-2";
        const string ValidModel3 = "";

        // Act
        Assert.Throws<NotSupportedException>(() => new AzureOpenAITextToImageService(modelId: InvalidModel, endpoint: "https://az.com", apiKey: "abc"));

        // No exceptions for these
        var _ = new AzureOpenAITextToImageService(modelId: ValidModel1, endpoint: "https://az.com", apiKey: "abc");
        _ = new AzureOpenAITextToImageService(modelId: ValidModel2, endpoint: "https://az.com", apiKey: "abc");
        _ = new AzureOpenAITextToImageService(modelId: ValidModel3, endpoint: "https://az.com", apiKey: "abc");
    }

    [Fact(Skip = "Needs refactoring, decouple from Azure SDK implementation details")]
    public async Task ItGeneratesImagesAsync()
    {
        // TODO: I don't think this test provides any value. It's hard coded with OpenAIClient's internal
        // implementation details, which is part of Azure AI SDK. Rather than mocking the HTTP client passed
        // to OpenAIClient we should consider mocking Azure's OpenAIClient' GetImageGenerationsAsync() method.

        // Arrange
        using var generateResult = CreateResponseMessage(HttpStatusCode.Accepted, "image_generation_test_response.json");
        using var imageResult = CreateResponseMessage(HttpStatusCode.OK, "image_result_test_response.json");
        using var mockHttpClient = GetHttpClientMock(generateResult, imageResult);

        // The model ID must be empty when working with DallE2 (and DallE3 is not supported yet).
        const string EmptyModelId = "";

        var generation = new AzureOpenAITextToImageService("https://fake-endpoint/", EmptyModelId, "fake-api-key", mockHttpClient);

        // Act
        var result = await generation.GenerateImageAsync("description", 256, 256);

        // Assert
        Assert.NotNull(result);
    }

    /// <summary>
    /// Returns a mocked instance of <see cref="HttpClient"/>.
    /// </summary>
    /// <param name="generateResult">The <see cref="HttpResponseMessage"/> to return for text to image.</param>
    /// <param name="imageResult">The <see cref="HttpResponseMessage"/> to return for image result.</param>
    /// <returns>A mocked <see cref="HttpClient"/> instance.</returns>
    private static HttpClient GetHttpClientMock(HttpResponseMessage generateResult, HttpResponseMessage imageResult)
    {
        var httpClientHandler = new Mock<HttpClientHandler>();

        httpClientHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(request => request.RequestUri!.AbsolutePath.Contains("openai/images/generations:submit")),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(generateResult);

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
        response.Content = new StringContent(
            OpenAITestHelper.GetTestResponse(fileName),
            Encoding.UTF8,
            "application/json");
        return response;
    }
}
