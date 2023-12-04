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

    [Fact]
    public async Task MathTestAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathematician = new AgentBuilder()
                            .WithName("mathematician")
                            .WithDescription("An assistant that answers math problems.")
                            .WithInstructions("You are a mathematician.\n" +
                                              "No need to show your work, just give the answer to the math problem.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var thread = mathematician.CreateThread();

        var response = await thread.InvokeAsync("If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would you have?").ConfigureAwait(true);
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
                            .WithInstructions("You are a mathematician.\nNo need to show your work, just give the result to the math problem.\n. Results are not approximative.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var butler = new AgentBuilder()
                    .WithName("alfred")
                    .WithDescription("An AI butler that helps humans.")
                    .WithInstructions("You are an AI assistant.\nYou ar not subject to execute any function yourself, so please use avaiable agents.\nRespond like a butler.")
                    .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                    .WithLoggerFactory(this._loggerFactory)
                    .WithAgent(mathematician,
                        agentDescription: "A mathematician that resolves given maths problems.",
                        inputDescription: "The word mathematics problem to solve in 2-3 sentences.\n" +
                                          "Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it.")
                    .Build();

        var thread = butler.CreateThread();

        var response = await thread.InvokeAsync("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?").ConfigureAwait(true);
    }

    [Fact]
    public async Task ButlerTestFromYamlAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathematician = AgentBuilder.FromTemplate("./Assistants/Mathematician.yaml",
                azureOpenAIChatCompletionDeployment,
                azureOpenAIChatCompletionDeployment,
                azureOpenAIEndpoint,
                azureOpenAIKey,
                new[] {
                    KernelPluginFactory.CreateFromObject(new MathPlugin(), "math")
                },
                loggerFactory: this._loggerFactory);

        var butler = AgentBuilder.FromTemplate("./Assistants/Butler.yaml",
                           azureOpenAIChatCompletionDeployment,
                           azureOpenAIChatCompletionDeployment,
                           azureOpenAIEndpoint,
                           azureOpenAIKey,
                           assistants: new[] {
                               new AgentAssistantModel()
                               {
                                   Agent = mathematician,
                                   Description = "Resolves maths problems.",
                                   InputDescription = "The word problem to solve in 2-3 sentences.\n" +
                                                      "Do not give me the formula, just the problem.\n" +
                                                      "Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it."
                               }
                           },
                           loggerFactory: this._loggerFactory);

        var thread = butler.CreateThread();

        _ = await thread.InvokeAsync("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?").ConfigureAwait(true);
        // If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, the future value of the investment would be approximately $66,332.44.
        _ = await thread.InvokeAsync("What if the rate is about 3.6%?").ConfigureAwait(true);
        // If you start with $25,000 in the stock market and leave it to grow for 20 years at a 3.6% interest rate, the future value of the investment would be approximately $50,714.85.
        _ = await thread.InvokeAsync("What interest rate is needed to reach a future value of $50,000 in 25 years?").ConfigureAwait(true);
        // To grow $25,000 to $50,000 in 25 years, you would need an annual interest rate of approximately 2.74%.
    }
}
