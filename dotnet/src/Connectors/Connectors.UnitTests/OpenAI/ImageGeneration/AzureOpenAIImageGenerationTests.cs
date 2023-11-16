// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ImageGeneration;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIImageGenerationTests"/> class.
/// </summary>
public sealed class AzureOpenAIImageGenerationTests
{
    [Fact]
    public async Task ItShouldGenerateImageSuccussedAsync()
    {
        //Arrange

        using var mockHttpClient = OpenAITestHelper.StartMockHttpClient()
            .SetupResponse("openai/images/generations:submit", HttpStatusCode.Accepted, "image_generation_test_response.json")
            .SetupResponse("openai/operations/images", HttpStatusCode.OK, "image_result_test_response.json")
            .BuildClient();

        var generation = new AzureOpenAIImageGeneration("https://fake-endpoint/", "fake-api-key", mockHttpClient);

        //Act
        var result = await generation.GenerateImageAsync("description", 256, 256);

        //Assert
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ItShouldGenerateImageSuccussedUsingDALLE3Async()
    {
        //Arrange
        using var mockHttpClient = OpenAITestHelper.StartMockHttpClient()
            .SetupResponse("images/generations", HttpStatusCode.Accepted, "dalle_3_image_generation_test_response.json")
            .BuildClient();

        var generation = new AzureOpenAIImageGeneration("deploymentName", "https://fake-endpoint", "fake-api-key", null, mockHttpClient);

        //Act
        var result = await generation.GenerateImageAsync("description", 1024, 1024);

        //Assert
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ItThrowOutOfRangeExceptionUsingDALLE2Async()
    {
        //Arrange

        using var mockHttpClient = OpenAITestHelper.StartMockHttpClient().BuildClient();

        var generation = new AzureOpenAIImageGeneration("https://fake-endpoint/", "fake-api-key", mockHttpClient);

        //Act
        //Assert

        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await generation.GenerateImageAsync("description", 100, 256);
        });
    }

    [Fact]
    public async Task ItThrowOutOfRangeExceptionUsingDALLE3Async()
    {
        //Arrange

        using var mockHttpClient = OpenAITestHelper.StartMockHttpClient().BuildClient();

        var generation = new AzureOpenAIImageGeneration("deployment", "https://fake-endpoint/", "fake-api-key", null, mockHttpClient);

        //Act
        //Assert

        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await generation.GenerateImageAsync("description", 100, 256);
        });
    }
}
