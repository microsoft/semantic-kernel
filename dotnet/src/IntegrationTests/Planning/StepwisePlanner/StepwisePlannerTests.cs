// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning.Stepwise;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.StepwisePlanner;

public sealed class StepwisePlannerTests : IDisposable
{
    private readonly string _bingApiKey;

    public StepwisePlannerTests(ITestOutputHelper output)
    {
        this._loggerFactory = NullLoggerFactory.Instance;
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

    [Theory]
    [InlineData(false, "Who is the current president of the United States? What is his current age divided by 2", "ExecutePlan", "StepwisePlanner")]
    [InlineData(true, "Who is the current president of the United States? What is his current age divided by 2", "ExecutePlan", "StepwisePlanner")]
    public void CanCreateStepwisePlan(bool useChatModel, string prompt, string expectedFunction, string expectedSkill)
    {
        // Arrange
        bool useEmbeddings = false;
        IKernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEngineSkill = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new TimePlugin(), "time");

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel, new StepwisePlannerConfig() { MaxIterations = 10 });

        // Act
        var plan = planner.CreatePlan(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.SkillName.Contains(expectedSkill, StringComparison.OrdinalIgnoreCase));
    }

    [Theory]
    [InlineData(false, "What is the tallest mountain on Earth? How tall is it divided by 2", "Everest")]
    [InlineData(true, "What is the tallest mountain on Earth? How tall is it divided by 2", "Everest")]
    [InlineData(false, "What is the weather in Seattle?", "Seattle", 1)]
    [InlineData(true, "What is the weather in Seattle?", "Seattle", 1)]
    public async void CanExecuteStepwisePlan(bool useChatModel, string prompt, string partialExpectedAnswer, int expectedMinSteps = 1)
    {
        // Arrange
        bool useEmbeddings = false;
        IKernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEngineSkill = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new TimePlugin(), "time");

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel, new StepwisePlannerConfig() { MaxIterations = 10 });

        // Act
        var plan = planner.CreatePlan(prompt);
        var result = await plan.InvokeAsync(kernel);

        // Assert - should contain the expected answer
        Assert.Contains(partialExpectedAnswer, result.Result, StringComparison.InvariantCultureIgnoreCase);

        Assert.True(result.Variables.TryGetValue("stepsTaken", out string? stepsTakenString));
        var stepsTaken = JsonSerializer.Deserialize<List<SystemStep>>(stepsTakenString!);
        Assert.NotNull(stepsTaken);
        Assert.True(stepsTaken.Count >= expectedMinSteps && stepsTaken.Count <= 10, $"Actual: {stepsTaken.Count}. Expected at least {expectedMinSteps} steps and at most 10 steps to be taken.");
    }

    private IKernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._loggerFactory);

        if (useChatModel)
        {
            builder.WithAzureChatCompletionService(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder.WithAzureTextEmbeddingGenerationService(
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey)
                .WithMemoryStorage(new VolatileMemoryStore());
        }

        var kernel = builder.Build();

        return kernel;
    }

    private readonly ILoggerFactory _loggerFactory;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~StepwisePlannerTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._loggerFactory is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}
