// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Stepwise;
public sealed class FunctionCallingStepwisePlannerTests : IDisposable
{
    private readonly string _bingApiKey;

    public FunctionCallingStepwisePlannerTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

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
    [InlineData("What is the tallest mountain on Earth? How tall is it?", new string[] { "WebSearch-Search" })]
    [InlineData("What is the weather in Seattle?", new string[] { "WebSearch-Search" })]
    [InlineData("What is the current hour number, plus 5?", new string[] { "Time-HourNumber", "Math-Add" })]
    [InlineData("What is 387 minus 22? Email the solution to John and Mary.", new string[] { "Math-Subtract", "Email-GetEmailAddress", "Email-SendEmail" })]
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
            new FunctionCallingStepwisePlannerOptions() { MaxIterations = 10 });

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

    [RetryFact(typeof(HttpOperationException))]
    public async Task DoesNotThrowWhenPluginFunctionThrowsNonCriticalExceptionAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();

        var emailPluginFake = new ThrowingEmailPluginFake();
        kernel.Plugins.Add(
            KernelPluginFactory.CreateFromFunctions(
            "Email",
            new[] {
                KernelFunctionFactory.CreateFromMethod(emailPluginFake.WritePoemAsync),
                KernelFunctionFactory.CreateFromMethod(emailPluginFake.SendEmailAsync),
            }));

        var planner = new FunctionCallingStepwisePlanner(
            new FunctionCallingStepwisePlannerOptions() { MaxIterations = 5 });

        // Act
        var planResult = await planner.ExecuteAsync(kernel, "Email a poem about cats to test@example.com");

        // Assert - should contain the expected answer & function calls within the maximum iterations
        Assert.NotNull(planResult);
        Assert.True(planResult.Iterations > 0);
        Assert.True(planResult.Iterations <= 5);

        string serializedChatHistory = JsonSerializer.Serialize(planResult.ChatHistory);
        Assert.Contains("Email-WritePoem", serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Email-SendEmail", serializedChatHistory, StringComparison.InvariantCultureIgnoreCase);
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task ThrowsWhenPluginFunctionThrowsCriticalExceptionAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();

        var emailPluginFake = new ThrowingEmailPluginFake();
        kernel.Plugins.Add(
            KernelPluginFactory.CreateFromFunctions(
            "Email",
            new[] {
                KernelFunctionFactory.CreateFromMethod(emailPluginFake.WriteJokeAsync),
                KernelFunctionFactory.CreateFromMethod(emailPluginFake.SendEmailAsync),
            }));

        var planner = new FunctionCallingStepwisePlanner(
            new FunctionCallingStepwisePlannerOptions() { MaxIterations = 5 });

        // Act & Assert
        // Planner should call ThrowingEmailPluginFake.WriteJokeAsync, which throws InvalidProgramException
        await Assert.ThrowsAsync<InvalidProgramException>(async () => await planner.ExecuteAsync(kernel, "Email a joke to test@example.com"));
    }

    private Kernel InitializeKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ILoggerFactory>(this._logger);
        builder.AddOpenAIChatCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey);

        var kernel = builder.Build();

        return kernel;
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;
    private readonly XunitLogger<Kernel> _logger;

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
            this._logger.Dispose();
            this._testOutputHelper.Dispose();
        }
    }
}
