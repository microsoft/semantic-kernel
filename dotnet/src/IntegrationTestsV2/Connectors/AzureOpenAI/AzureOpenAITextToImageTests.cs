// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextToImage;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTestsV2.Connectors.AzureOpenAI;

public sealed class AzureOpenAITextToImageTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAITextToImageTests>()
        .Build();

    [Fact]
    public async Task ItCanReturnImageUrlAsync()
    {
        // Arrange
        AzureOpenAIConfiguration? configuration = this._configuration.GetSection("AzureOpenAITextToImage").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextToImage(configuration.DeploymentName, configuration.Endpoint, configuration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 1024, 1024);

        // Assert
        Assert.NotNull(result);
        Assert.StartsWith("https://", result);
    }
}
