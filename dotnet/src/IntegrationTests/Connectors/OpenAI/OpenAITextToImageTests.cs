// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextToImage;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

#pragma warning disable CS0618 // Type or member is obsolete

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAITextToImageTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAITextToImageTests>()
        .Build();

    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("gpt-image-1", 1024, 1024)]
    public async Task OpenAITextToImageByModelTestAsync(string modelId, int width, int height)
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey, modelId: modelId)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", width, height);

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }

    [Fact(Skip = "Failing in integration tests pipeline with - HTTP 400 (invalid_request_error: billing_hard_limit_reached) error.")]
    public async Task OpenAITextToImageUseDefaultModelAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 1024, 1024);

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }

    [Fact(Skip = "Failing in integration tests pipeline with - HTTP 400 (invalid_request_error: billing_hard_limit_reached) error.")]
    public async Task OpenAITextToImageGetImagesTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey, modelId: "gpt-image-1")
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GetImageContentsAsync("The sun rises in the east and sets in the west.", new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
        var imageContent = result[0];
        Assert.True(imageContent.Uri is not null || imageContent.Data is not null, "Image content should have either a URI or binary data.");
    }
}
