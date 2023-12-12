// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit.Abstractions;
using Xunit;
using SemanticKernel.IntegrationTests.Fakes;
using System.Text.Json;

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
            .AddUserSecrets<FunctionCallingStepwisePlannerTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Theory(Skip = "Requires model deployment that supports function calling.")]
    [InlineData("What is the tallest mountain on Earth? How tall is it?", "Everest", new string[] { "WebSearch_Search" })]
    [InlineData("What is the weather in Seattle?", "Seattle", new string[] { "WebSearch_Search" })]
    [InlineData("What is the current hour number, plus 5?", "", new string[] { "Time_HourNumber", "Math_Add" })]
    [InlineData("What is 387 minus 22? Email the solution to John and Mary.", "365", new string[] { "Math_Subtract", "Email_GetEmailAddress", "Email_SendEmail" })]
    public async Task CanExecuteStepwisePlanAsync(string prompt, string partialExpectedAnswer, string[] expectedFunctions)
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        kernel.ImportPluginFromObject(webSearchEnginePlugin, "WebSearch");
        kernel.ImportPluginFromType<TimePlugin>("Time");
        kernel.ImportPluginFromType<MathPlugin>("Math");
        kernel.ImportPluginFromType<EmailPluginFake>("Email");

        var planner = new FunctionCallingStepwisePlanner(
            new FunctionCallingStepwisePlannerConfig() { MaxIterations = 10 });

        // Act
        var planResult = await planner.ExecuteAsync(kernel, prompt);

        // Assert - should contain the expected answer & function calls within the maximum iterations
        Assert.NotNull(planResult);
        Assert.NotEqual(string.Empty, planResult.FinalAnswer);
        Assert.True(planResult.Iterations > 0);
        Assert.True(planResult.Iterations <= 10);
        Assert.Contains(partialExpectedAnswer, planResult.FinalAnswer, StringComparison.InvariantCultureIgnoreCase);

        string serializedChatHistory = JsonSerializer.Serialize(planResult.ChatHistory);
        foreach (string expectedFunction in expectedFunctions)
        {
            Assert.Contains(expectedFunction, serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
        }
    }

    private Kernel InitializeKernel()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);

        var kernel = builder.Build();

        return kernel;
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~FunctionCallingStepwisePlannerTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._testOutputHelper.Dispose();
        }
    }
}
