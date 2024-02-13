// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAITextToAudioTests : IDisposable
{
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public OpenAITextToAudioTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAITextToAudioTests>()
            .Build();
    }

    [Fact(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    public async Task OpenAITextToAudioTestAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAITextToAudio").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var service = new OpenAITextToAudioService(openAIConfiguration.ModelId, openAIConfiguration.ApiKey);

        // Act
        var result = await service.GetAudioContentAsync("The sun rises in the east and sets in the west.", new OpenAITextToAudioExecutionSettings("alloy"));

        // Assert
        Assert.NotNull(result?.Data);
        Assert.False(result.Data.IsEmpty);
    }

    [Fact]
    public async Task AzureOpenAITextToAudioTestAsync()
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAITextToAudio").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var service = new AzureOpenAITextToAudioService(
            azureOpenAIConfiguration.DeploymentName,
            azureOpenAIConfiguration.Endpoint,
            azureOpenAIConfiguration.ApiKey);

        // Act
        var result = await service.GetAudioContentAsync("The sun rises in the east and sets in the west.", new OpenAITextToAudioExecutionSettings("alloy"));

        // Assert
        Assert.NotNull(result?.Data);
        Assert.False(result.Data.IsEmpty);
    }

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
