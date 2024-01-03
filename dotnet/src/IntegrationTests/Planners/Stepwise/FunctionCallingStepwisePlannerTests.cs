// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.Fakes;
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
            .AddUserSecrets<FunctionCallingStepwisePlannerTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Theory]
    [InlineData("What is the tallest mountain on Earth? How tall is it?", new string[] { "WebSearch_Search" })]
    [InlineData("What is the weather in Seattle?", new string[] { "WebSearch_Search" })]
    [InlineData("What is the current hour number, plus 5?", new string[] { "Time_HourNumber", "Math_Add" })]
    [InlineData("What is 387 minus 22? Email the solution to John and Mary.", new string[] { "Math_Subtract", "Email_GetEmailAddress", "Email_SendEmail" })]
    public async Task CanExecuteStepwisePlanAsync(string prompt, string[] expectedFunctions)
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
        Assert.NotEmpty(planResult.FinalAnswer);

        string serializedChatHistory = JsonSerializer.Serialize(planResult.ChatHistory);
        foreach (string expectedFunction in expectedFunctions)
        {
            Assert.Contains(expectedFunction, serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
        }
    }

    [Fact]
    public async Task DoesNotThrowWhenPluginFunctionThrowsNonCriticalExceptionAsync()
    {
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<ThrowingEmailPluginFake>("Email");

        var planner = new FunctionCallingStepwisePlanner(
            new FunctionCallingStepwisePlannerConfig() { MaxIterations = 5 });

        // Act
        var planResult = await planner.ExecuteAsync(kernel, "Email a poem about cats to test@example.com");

        // Assert - should contain the expected answer & function calls within the maximum iterations
        Assert.NotNull(planResult);
        Assert.True(planResult.Iterations > 0);
        Assert.True(planResult.Iterations <= 5);

        string serializedChatHistory = JsonSerializer.Serialize(planResult.ChatHistory);
        Assert.Contains("Email_WritePoem", serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Email_SendEmail", serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ThrowsWhenPluginFunctionThrowsCriticalExceptionAsync()
    {
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<ThrowingEmailPluginFake>("Email");

        var planner = new FunctionCallingStepwisePlanner(
            new FunctionCallingStepwisePlannerConfig() { MaxIterations = 5 });

        // Act & Assert
        // Planner should call ThrowingEmailPluginFake.GetEmailAddressAsync, which throws InvalidProgramException
        await Assert.ThrowsAsync<InvalidProgramException>(async () => await planner.ExecuteAsync(kernel, "What is Kelly's email address?"));
    }

    private Kernel InitializeKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey);

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
