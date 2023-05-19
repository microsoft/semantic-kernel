// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using Planning.IterativePlanner;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.Iterative;

public sealed class IterativePlannerChatTests : IDisposable
{
    public IterativePlannerChatTests(ITestOutputHelper output)
    {
        this._logger = new RedirectOutput(output);
        this._testOutputHelper = output;

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<IterativePlannerChatTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Fact]
    public async Task CanCorrectlyParseLongConversationAsync()
    {
        // the purpose of this test it to ensure that even for long conversations
        // the result is still generated correctly and it can be properly parsed

        // Arrange
        IKernel kernel = this.InitializeKernel("gpt-35-turbo");
        //lets limit it to 10 steps to have a long chain and scratchpad
        var plan = new IterativePlannerChat(kernel, 12, logger: this._logger);
        var goal = "count down from 10 to one using subtraction functionality of the calculator tool. Decrementing value by 1 in each step. Each step should have only one subtraction. So you need to call calculator tool multiple times ";
        var result = await plan.ExecutePlanAsync(goal);

        // Assert
        this.PrintPlan(plan, result);
        //there should be text final in the result
        Assert.Contains("1", result);
        //there should be at least 9 steps, sometiems it will calculate 2-1 by itself
        Assert.True(plan.Steps.Count >= 9, "it should take at least 9 steps");
    }

    private void PrintPlan(IterativePlannerText plan, string result)
    {
        foreach (var step in plan.Steps)
        {
            this._testOutputHelper.WriteLine("a: " + step.Action);
            this._testOutputHelper.WriteLine("ai: " + step.ActionInput);
            this._testOutputHelper.WriteLine("t: " + step.Thought);
            this._testOutputHelper.WriteLine("o: " + step.Observation);
            this._testOutputHelper.WriteLine("--");
        }

        this._testOutputHelper.WriteLine("Result:" + result);
    }

    [Fact]
    public async Task CanExecuteSimpleIterativePlanAsync()
    {
        // Arrange
        IKernel kernel = this.InitializeKernel("gpt-35-turbo");
        //it should be able to finish in 4 steps 
        var plan = new IterativePlannerChat(kernel, 5, logger: this._logger);
        var goal = "Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?";
        //var goal = "Who is Leo DiCaprio's girlfriend? What is her current age ?";

        // Act
        var result = await plan.ExecutePlanAsync(goal);
        this._testOutputHelper.WriteLine(result);

        // Debug and show all the steps and actions
        this.PrintPlan(plan, result);

        // Assert
        // first step should be a search for girlfriend
        var firstStep = plan.Steps[0];
        Assert.Equal("Search", firstStep.Action);
        Assert.Contains("girlfriend", firstStep.Thought);

        ////// second step should be a search for age of the girlfriend
        //var secondStep = plan.Steps[1];
        //Assert.Equal("Search", secondStep.Action);
        //Assert.Contains("age", secondStep.Thought);

        //search is not predictable sometimes it will return a reference to the age
        int countCalculator = plan.Steps.Count(x => x.Action?.ToLower() == "calculator");
        Assert.True(countCalculator > 0, "at least once calculator");
    }

    private IKernel InitializeKernel(string? deploymentName = null)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        //OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var x = deploymentName ?? azureOpenAIConfiguration.DeploymentName;
        var builder = Kernel.Builder
            .WithLogger(this._logger)
            .Configure(config =>
            {
                config.AddAzureChatCompletionService(
                    deploymentName: deploymentName ?? azureOpenAIConfiguration.DeploymentName,
                    endpoint: azureOpenAIConfiguration.Endpoint,
                    apiKey: azureOpenAIConfiguration.ApiKey);
            });

        //var builder = Kernel.Builder
        //    .WithLogger(this._logger)
        //    .Configure(config =>
        //    {
        //        //config.AddOpenAIChatCompletionService("gpt-3.5-turbo", openAIConfiguration.ApiKey);
        //        config.AddOpenAIChatCompletionService("gpt-4", openAIConfiguration.ApiKey);
        //    });

        //kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));
        var kernel = builder.Build();

        BingConnector connector = new(this._bingApiKey);

        var webSearchEngineSkill = new WebSearchSkill(connector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");

        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "calculator");

        return kernel;
    }

    private readonly RedirectOutput _logger;
    private readonly ITestOutputHelper _testOutputHelper;
    private readonly IConfigurationRoot _configuration;
    private string _bingApiKey;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~IterativePlannerChatTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._logger is IDisposable ld)
            {
                ld.Dispose();
            }

            this._logger.Dispose();
        }
    }
}
