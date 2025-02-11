// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Amazon.BedrockAgent.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with kernel functions.
/// </summary>
public class Step02_BedrockAgent_Functions(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string AgentName = "Semantic-Kernel-Test-Agent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private const string UserQuery = "What is the weather in Seattle?";

    [Fact]
    public async Task UseAgentWithFunctionsAsync()
    {
        // Define the agent
        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = AgentName,
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
            FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
        };

        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());

        var bedrock_agent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            kernel: kernel,
            enableKernelFunctions: true);

        // Respond to user input
        try
        {
            var responses = bedrock_agent.InvokeAsync(BedrockAgent.CreateSessionId(), UserQuery, null, CancellationToken.None);
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

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
        // [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }
    }
}
