// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi.OpenAI;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Stepwise;

public sealed class StepwisePlannerTests : IDisposable
{
    private readonly string _bingApiKey;

    public StepwisePlannerTests(ITestOutputHelper output)
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

    [Theory]
    [InlineData(false, "Who is the current president of the United States? What is his current age divided by 2", "ExecutePlan", "StepwisePlanner")]
    [InlineData(true, "Who is the current president of the United States? What is his current age divided by 2", "ExecutePlan", "StepwisePlanner")]
    public void CanCreateStepwisePlanAsync(bool useChatModel, string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        Kernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportPluginFromObject(webSearchEnginePlugin, "WebSearch");
        kernel.ImportPluginFromType<TimePlugin>("time");

        var planner = new StepwisePlanner(kernel, new() { MaxIterations = 10 });

        // Act
        var plan = planner.CreatePlan(prompt);

        // Assert
        Assert.Empty(plan.Steps);
        Assert.Equal(expectedFunction, plan.Name);
        Assert.Contains(expectedPlugin, plan.PluginName, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(maxRetries: 3)]
    [InlineData(false, "What is the tallest mountain on Earth? How tall is it divided by 2", "Everest")]
    [InlineData(true, "What is the tallest mountain on Earth? How tall is it divided by 2", "Everest")]
    [InlineData(false, "What is the weather in Seattle?", "Seattle")]
    [InlineData(true, "What is the weather in Seattle?", "Seattle")]
    public async Task CanExecuteStepwisePlanAsync(bool useChatModel, string prompt, string partialExpectedAnswer)
    {
        // Arrange
        bool useEmbeddings = false;
        Kernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportPluginFromObject(webSearchEnginePlugin, "WebSearch");
        kernel.ImportPluginFromType<TimePlugin>("time");

        var planner = new StepwisePlanner(kernel, new() { MaxIterations = 10 });

        // Act
        var plan = planner.CreatePlan(prompt);
        var planResult = await plan.InvokeAsync(kernel);
        var result = planResult.GetValue<string>();

        // Assert - should contain the expected answer
        Assert.NotNull(result);
        Assert.Contains(partialExpectedAnswer, result, StringComparison.InvariantCultureIgnoreCase);
        Assert.True(planResult.TryGetMetadataValue("iterations", out string iterations));
        Assert.True(int.Parse(iterations, System.Globalization.CultureInfo.InvariantCulture) > 0);
        Assert.True(int.Parse(iterations, System.Globalization.CultureInfo.InvariantCulture) <= 10);
    }

    [Fact]
    public async Task ExecutePlanFailsWithTooManyFunctionsAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportPluginFromObject(webSearchEnginePlugin, "WebSearch");
        kernel.ImportPluginFromType<TextPlugin>("text");
        kernel.ImportPluginFromType<ConversationSummaryPlugin>("ConversationSummary");
        kernel.ImportPluginFromType<MathPlugin>("Math");
        kernel.ImportPluginFromType<FileIOPlugin>("FileIO");
        kernel.ImportPluginFromType<HttpPlugin>("Http");

        var planner = new StepwisePlanner(kernel, new() { MaxTokens = 1000 });

        // Act
        var plan = planner.CreatePlan("I need to buy a new brush for my cat. Can you show me options?");

        // Assert
        var ex = await Assert.ThrowsAsync<KernelException>(async () => await plan.InvokeAsync(kernel));
        Assert.Equal("ChatHistory is too long to get a completion. Try reducing the available functions.", ex.Message);
    }

    [Fact]
    public async Task ExecutePlanSucceedsWithAlmostTooManyFunctionsAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();

        _ = await kernel.ImportPluginFromOpenAIAsync("Klarna", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenAIFunctionExecutionParameters(enableDynamicOperationPayload: true));

        var planner = new StepwisePlanner(kernel);

        // Act
        var plan = planner.CreatePlan("I need to buy a new brush for my cat. Can you show me options?");
        var functionResult = await plan.InvokeAsync(kernel);
        var result = functionResult.GetValue<string>();

        // Assert - should contain results, for now just verify it didn't fail
        Assert.NotNull(result);
        Assert.DoesNotContain("Result not found, review 'stepsTaken' to see what happened", result, StringComparison.OrdinalIgnoreCase);
    }

    private Kernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();

        if (useChatModel)
        {
            builder.Services.AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.Services.AddAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder.Services.AddAzureOpenAITextEmbeddingGeneration(
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
