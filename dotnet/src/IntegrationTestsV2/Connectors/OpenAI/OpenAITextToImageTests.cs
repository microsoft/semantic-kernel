// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextToImage;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;
public sealed class OpenAITextToImageTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAITextToImageTests>()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OpenAITextToImageTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(modelId: openAIConfiguration.ModelId, apiKey: openAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 512, 512);

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OpenAITextToImageByModelTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(modelId: openAIConfiguration.ModelId, apiKey: openAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 1024, 1024);

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }
}
