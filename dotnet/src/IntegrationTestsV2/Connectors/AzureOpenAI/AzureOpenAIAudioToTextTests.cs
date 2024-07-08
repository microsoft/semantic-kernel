// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTestsV2.Connectors.AzureOpenAI;

public sealed class AzureOpenAIAudioToTextTests()
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIAudioToTextTests>()
        .Build();

    [Fact]
    public async Task AzureOpenAIAudioToTextTestAsync()
    {
        // Arrange
        const string Filename = "test_audio.wav";

        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAIAudioToText").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIAudioToText(
                azureOpenAIConfiguration.DeploymentName,
                azureOpenAIConfiguration.Endpoint,
                azureOpenAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<IAudioToTextService>();

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var audioData = await BinaryData.FromStreamAsync(audio);

        // Act
        var result = await service.GetTextContentAsync(new AudioContent(audioData, mimeType: "audio/wav"), new OpenAIAudioToTextExecutionSettings(Filename));

        // Assert
        Assert.Contains("The sun rises in the east and sets in the west.", result.Text, StringComparison.OrdinalIgnoreCase);
    }
}
