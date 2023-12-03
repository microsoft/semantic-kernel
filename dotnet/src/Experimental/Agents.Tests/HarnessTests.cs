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
                            .WithInstructions("You are a mathmatician.\nNo need to show your work, just give the answer to the math problem.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var thread = mathematician.CreateThread();

        var response = await thread.InvokeAsync("If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would you have? Expand the following expression: 7(3y+2)").ConfigureAwait(true);
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
                            .WithInstructions("You are a mathematician.\nNo need to show your work, just give the answer to the math problem.\nResults are not approximative.")
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .WithPlugin(KernelPluginFactory.CreateFromObject(new MathPlugin(), "math"))
                            .WithLoggerFactory(this._loggerFactory)
                            .Build();

        var butler = new AgentBuilder()
                    .WithName("alfred")
                    .WithDescription("An AI butler that helps humans.")
                    .WithInstructions("You are an AI assistant.\nOnly use available agent or plugin to answer questions.\nRespond as a butler.")
                    .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                    .WithLoggerFactory(this._loggerFactory)
                    .WithAgent(mathematician,
                        agentDescription: "Agent that resolves maths problems.",
                        inputDescription: "The word problem to solve in 2-3 sentences. Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it.")
                    .Build();

        var thread = butler.CreateThread();

        var response = await thread.InvokeAsync("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have? Expand the following expression: 7(3y+2)").ConfigureAwait(true);
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
                                   InputDescription = "The word problem to solve in 2-3 sentences. Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it."
                               }
                           },
                           loggerFactory: this._loggerFactory);

        var thread = butler.CreateThread();

        var response = await thread.InvokeAsync("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?\nExpand the following expression: 7(3y+2)").ConfigureAwait(true);
    }
}
