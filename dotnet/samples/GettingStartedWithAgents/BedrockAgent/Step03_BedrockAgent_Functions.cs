﻿// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with kernel functions.
/// </summary>
public class Step03_BedrockAgent_Functions(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it.
    /// The agent will respond to the user query by calling kernel functions to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentWithFunctionsAsync()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions");

        // Respond to user input
        try
        {
            var responses = bedrockAgent.InvokeAsync(
                BedrockAgent.CreateSessionId(),
                "What is the weather in Seattle?",
                null);
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
            await this.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it using streaming.
    /// The agent will respond to the user query by calling kernel functions to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentStreamingWithFunctionsAsync()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Streaming");

        // Respond to user input
        try
        {
            var streamingResponses = bedrockAgent.InvokeStreamingAsync(
                BedrockAgent.CreateSessionId(),
                "What is the weather forecast in Seattle?",
                null);
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
            await this.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it.
    /// The agent will respond to the user query by calling multiple kernel functions in parallel to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentWithParallelFunctionsAsync()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Parallel");

        // Respond to user input
        try
        {
            var responses = bedrockAgent.InvokeAsync(
                BedrockAgent.CreateSessionId(),
                "What is the current weather in Seattle and what is the weather forecast in Seattle?",
                null);
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
            await this.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new kernel with plugins
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client)
        {
            Kernel = kernel,
        };
        // Create the kernel function action group and prepare the agent for interaction
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();

        return bedrockAgent;
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
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
