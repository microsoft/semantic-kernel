// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Agents.Tests;

public class HarnessTests
{
    private readonly ITestOutputHelper _output;

    public HarnessTests(ITestOutputHelper output)
    {
        this._output = output;
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
                            .WithKernel(new KernelBuilder()
                                    .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                                    .Build())
                            .Build();

        var thread = assistant.CreateThread("Eggs are yummy and beautiful geometric gems.");

        var response = await thread.InvokeAsync().ConfigureAwait(true);

        this._output.WriteLine(thread.ToString());
    }

    [Fact]
    public async Task MathTestAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathPlugin = new MathPlugin();

        var mathKernel = new KernelBuilder()
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .Build();

        mathKernel.ImportPluginFromObject(mathPlugin, "math");

        var webSearcher = new AgentBuilder()
                            .WithName("mathmatician")
                            .WithDescription("An assistant that answers math problems.")
                            .WithInstructions("You are a mathmatician. No need to show your work, just give the answer to the math problem\nThe answer to the math problem \"{{ask}}\" is {{Math_PerformMath math_word_problem=ask}}.\r\n")
                            .WithKernel(mathKernel)
                            .Build();

        var thread = webSearcher.CreateThread("If you start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would you have? Expand the following expression: 7(3y+2)");

        var response = await thread.InvokeAsync().ConfigureAwait(true);

        this._output.WriteLine(thread.ToString());
    }

    [Fact]
    public async Task ButlerTestAsync()
    {
        string azureOpenAIKey = TestConfig.AzureOpenAIAPIKey;
        string azureOpenAIEndpoint = TestConfig.AzureOpenAIEndpoint;
        string azureOpenAIChatCompletionDeployment = TestConfig.AzureOpenAIDeploymentName;

        var mathPlugin = new MathPlugin();

        var mathKernel = new KernelBuilder()
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .Build();

        var butlerKernel = new KernelBuilder()
                            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
                            .Build();

        mathKernel.ImportPluginFromObject(mathPlugin, "math");

        var mathmatician = new AgentBuilder()
                            .WithName("mathmatician")
                            .WithDescription("An assistant that answers math problems with a given user prompt.")
                            .WithInstructions("You are a mathmatician. No need to show your work, just give the answer to the math problem\nThe answer to the math problem \"{{ask}}\" is {{Math_PerformMath math_word_problem=ask}}.\r\n")
                            .WithKernel(mathKernel)
                            .Build();

        var butler = new AgentBuilder()
                    .WithName("jarvis")
                    .WithDescription("A butler that helps humans.")
                    .WithInstructions("Act as a butler.\nProvide feedback or advice to the user if needed.\nContact agents if necessary. Respond to user like jarvis from Iron man.")
                    .WithKernel(butlerKernel)
                    .WithAgent(mathmatician)
                    .Build();

        var thread = butler.CreateThread("If I start with $25,000 in the stock market and leave it to grow for 20 years at a 5% interest rate, how much would I have?");

        var response = await thread.InvokeAsync().ConfigureAwait(true);

        this._output.WriteLine(thread.ToString());
    }
}
