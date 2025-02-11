// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with kernel functions.
/// </summary>
public class Step02_BedrockAgent_Functions(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    [Fact]
    public async Task UseAgentWithFunctionsAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions");

        // Respond to user input
        try
        {
            var responses = bedrock_agent.InvokeAsync(
                BedrockAgent.CreateSessionId(),
                "What is the weather in Seattle?",
                null,
                CancellationToken.None);
            await foreach (var response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    [Fact]
    public async Task UseAgentStreamingWithFunctionsAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Streaming");

        // Respond to user input
        try
        {
            var streamingResponses = bedrock_agent.InvokeStreamingAsync(
                BedrockAgent.CreateSessionId(),
                "What is the weather forecast in Seattle?",
                null,
                CancellationToken.None);
            await foreach (var response in streamingResponses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    [Fact]
    public async Task UseAgentWithParallelFunctionsAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Parallel");

        // Respond to user input
        try
        {
            var responses = bedrock_agent.InvokeAsync(
                BedrockAgent.CreateSessionId(),
                "What is the current weather in Seattle and what is the weather forecast in Seattle?",
                null,
                CancellationToken.None);
            await foreach (var response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());

        return await BedrockAgent.CreateAsync(
            this.GetCreateAgentRequest(agentName),
            kernel: kernel,
            enableKernelFunctions: true);
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
        // [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }

        [KernelFunction, Description("Forecast weather information.")]
        public string Forecast([Description("The location to get the weather for.")] string location)
        {
            return $"The forecast for {location} is 75 degrees tomorrow.";
        }
    }
}
