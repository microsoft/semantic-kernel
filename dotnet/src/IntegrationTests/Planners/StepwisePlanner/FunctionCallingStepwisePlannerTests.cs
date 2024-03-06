// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Stepwise;

public sealed class FunctionCallingStepwisePlannerTests : IDisposable
{
    private readonly string _bingApiKey;

    public FunctionCallingStepwisePlannerTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<StepwisePlannerTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Theory(Skip = "Requires model deployment that supports function calling.")]
    [InlineData("What is the tallest mountain on Earth? How tall is it?", "Everest")]
    [InlineData("What is the weather in Seattle?", "Seattle")]
    public async Task CanExecuteStepwisePlanAsync(string prompt, string partialExpectedAnswer)
    {
        // Arrange
        bool useEmbeddings = false;
        Kernel kernel = this.InitializeKernel(useEmbeddings);
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportPluginFromObject(webSearchEnginePlugin, "WebSearch");
        kernel.ImportPluginFromType<TimePlugin>("time");

        var planner = new FunctionCallingStepwisePlanner(
            kernel,
            new FunctionCallingStepwisePlannerConfig() { MaxIterations = 10 });

        // Act
        var planResult = await planner.ExecuteAsync(prompt);

        // Assert - should contain the expected answer
        Assert.NotNull(planResult);
        Assert.NotEqual(string.Empty, planResult.FinalAnswer);
        Assert.Contains(partialExpectedAnswer, planResult.FinalAnswer, StringComparison.InvariantCultureIgnoreCase);
        Assert.True(planResult.Iterations > 0);
        Assert.True(planResult.Iterations <= 10);
    }

    private Kernel InitializeKernel(bool useEmbeddings = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.CreateBuilder()
            .WithAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        if (useEmbeddings)
        {
            builder.WithAzureOpenAITextEmbeddingGeneration(
                deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
        }

        return builder.Build();
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
