// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Agents.Tests;

public class HarnessTests
{
    private readonly ITestOutputHelper _output;

    private readonly ILoggerFactory _loggerFactory;

    public HarnessTests(ITestOutputHelper output)
    {
        this._output = output;

        this._loggerFactory = LoggerFactory.Create(logging =>
        {
            logging
                .AddProvider(new XunitLoggerProvider(output))
                .AddConfiguration(TestConfig.Configuration.GetSection("Logging"));
        });
    }

    [Fact]
    public async Task PoetTestAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var assistant = new AgentBuilder()
                            .WithName("poet")
                            .WithDescription("An assistant that create sonnet poems.")
                            .WithInstructions("You are a poet that composes poems based on user input.\nCompose a sonnet inspired by the user input.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var thread = assistant.CreateThread();

        var response = await thread.InvokeAsync("Eggs are yummy and beautiful geometric gems.").ConfigureAwait(true);
    }

    [Theory]
    [InlineData("What is the square root of 4?")]
    [InlineData("If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would you have?")]
    public async Task MathCalculationTestsAsync(string prompt)
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathematician = new AgentBuilder()
                            .WithName("mathematician")
                            .WithDescription("An assistant that answers math problems.")
                            .WithInstructions("You are a mathematician.\n" +
                                              "No need to show your work, just give the answer to the math problem.\n" +
                                              "Use calculation results.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var thread = mathematician.CreateThread();

        var response = await thread.InvokeAsync(prompt).ConfigureAwait(true);
    }

    [Fact]
    public async Task ButlerTestAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathematician = new AgentBuilder()
                            .WithName("mathematician")
                            .WithDescription("An assistant that answers math problems with a given user prompt.")
                            .WithInstructions("You are a mathematician.\n" +
                                              "No need to show your work, just give the answer to the math problem.\n" +
                                              "Use calculation results.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var butler = new AgentBuilder()
                    .WithName("alfred")
                    .WithDescription("An AI butler that helps humans.")
                    .WithInstructions("Act as a butler.\nNo need to explain further the internal process.\nBe concise when answering.")
                    .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                    .WithLoggerFactory(this._loggerFactory)
                    .WithAgent(mathematician,
                        agentDescription: "A mathematician that resolves given maths problems.",
                        inputDescription: "The word mathematics problem to solve in 2-3 sentences.\n" +
                                          "Important: Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it.")
                    .Build();

        var thread = butler.CreateThread();

        var response = await thread.InvokeAsync("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?").ConfigureAwait(true);
    }

    [Fact]
    public async Task FinancialAdvisorFromTemplateTestsAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathematician = AgentBuilder.FromTemplate("./Assistants/Mathematician.yaml",
                azureOpenAIEndpoint,
                azureOpenAIKey,
                new[] {
                    KernelPluginFactory.CreateFromObject(new MathPlugin(), "math")
                },
                loggerFactory: this._loggerFactory);

        var butler = AgentBuilder.FromTemplate("./Assistants/Butler.yaml",
                           azureOpenAIEndpoint,
                           azureOpenAIKey,
                           assistants: new[] {
                               new AgentAssistantModel()
                               {
                                   Agent = mathematician,
                                   Description = "A mathematician that resolves given maths problems.",
                                   InputDescription = "The word mathematics problem to solve in 2-3 sentences.\n" +
                                                      "Important: Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it."
                               }
                           },
                           loggerFactory: this._loggerFactory);



        var thread = butler.CreateThread();
        var question = "If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?";

        var result = await thread.InvokeAsync(question)
            .ConfigureAwait(true);

        await this.AuditorTestsAsync(question, result, "If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, the future value of the investment would be approximately $66,332.44.", true).ConfigureAwait(true);

        result = await thread.InvokeAsync("What if the rate is about 3.6%?").ConfigureAwait(true);
        await this.AuditorTestsAsync(question + "\nWhat if the rate is about 3.6%?", result, "If you start with $25,000 in the stock market and leave it to grow for 20 years at a 3.6% interest rate, the future value of the investment would be approximately $50,714.85.", true).ConfigureAwait(true);        
    }

    [Theory]
    [InlineData("What is the square root of 4?", "square result is 2", "2 is the square of 4.", true)]
    [InlineData("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?", "The future value of $25,000 invested at a 5% interest rate for 20 years would be approximately $66,332.44.", "If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, the future value of the investment would be approximately $66,332.44.", true)]
    [InlineData("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?", "If the interest rate is 3.6%, the future value of the $25,000 investment over 20 years would be approximately $47,688.04.", "If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, the future value of the investment would be approximately $66,332.44.", false)]
    public async Task AuditorTestsAsync(
        string question,
        string answer1,
        string answer2,
        bool equality)
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var verifier = AgentBuilder.FromTemplate("./Assistants/Auditor.yaml",
                  azureOpenAIEndpoint,
                  azureOpenAIKey,
                  loggerFactory: this._loggerFactory);

        Assert.Equal(equality, bool.Parse(await verifier.CreateThread()
            .InvokeAsync(
            $"Question: {question}\n" +
            $"Answer 1: {answer1}\n" +
            $"Answer 2: {answer2}")
                .ConfigureAwait(true)));
    }
}
