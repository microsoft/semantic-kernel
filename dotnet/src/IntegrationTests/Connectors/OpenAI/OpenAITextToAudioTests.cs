// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextToAudio;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAITextToAudioTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAITextToAudioTests>()
        .Build();

    [Fact] //(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    public async Task OpenAITextToAudioTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToAudio").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToAudio(openAIConfiguration.ModelId, openAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<ITextToAudioService>();

        // Act
        var result = await service.GetAudioContentAsync("The sun rises in the east and sets in the west.");

        // Assert
        var audioData = result.Data!.Value;
        Assert.False(audioData.IsEmpty);
    }
}
