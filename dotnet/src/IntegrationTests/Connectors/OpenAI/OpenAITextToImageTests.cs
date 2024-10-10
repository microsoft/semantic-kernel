// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using Microsoft.SemanticKernel.Connectors.OpenAI;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.Connectors.OpenAI;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using Microsoft.SemanticKernel.Connectors.OpenAI;
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.TextToImage;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
#pragma warning disable CS0618 // Type or member is obsolete

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
#pragma warning disable CS0618 // Type or member is obsolete

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
    [InlineData("dall-e-2", 512, 512)]
    [InlineData("dall-e-3", 1024, 1024)]
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

    [Fact]
    public async Task OpenAITextToImageUseDallE2ByDefaultAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey, modelId: null)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey, modelId: null)
=======
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 256, 256);

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

    [Fact]
    public async Task OpenAITextToImageDalle3GetImagesTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToImage").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(apiKey: openAIConfiguration.ApiKey, modelId: "dall-e-3")
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GetImageContentsAsync("The sun rises in the east and sets in the west.", new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
        Assert.NotEmpty(result[0].Uri!.ToString());
    }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
