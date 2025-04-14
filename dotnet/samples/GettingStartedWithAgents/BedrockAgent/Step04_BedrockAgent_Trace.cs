// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> and inspect the agent's thought process.
/// To learn more about different traces available, see:
/// https://docs.aws.amazon.com/bedrock/latest/userguide/trace-events.html
/// </summary>
public class Step04_BedrockAgent_Trace(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    /// <summary>
    /// Demonstrates how to inspect the thought process of a <see cref="BedrockAgent"/> by enabling trace.
    /// </summary>
    [Fact]
    public async Task UseAgentWithTrace()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step04_BedrockAgent_Trace");

        // Respond to user input
        var userQuery = "What is the current weather in Seattle and what is the weather forecast in Seattle?";
        try
        {
            AgentThread agentThread = new BedrockAgentThread(this.RuntimeClient);
            BedrockAgentInvokeOptions options = new()
            {
                EnableTrace = true,
            };

            var responses = bedrockAgent.InvokeAsync([new ChatMessageContent(AuthorRole.User, userQuery)], agentThread, options);
            await foreach (ChatMessageContent response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
                if (response.InnerContent is List<object?> innerContents)
                {
                    // There could be multiple traces and they are stored in the InnerContent property
                    var traceParts = innerContents.OfType<TracePart>().ToList();
                    if (traceParts is not null)
                    {
                        foreach (var tracePart in traceParts)
                        {
                            this.OutputTrace(tracePart.Trace);
                        }
                    }
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Outputs the trace information to the console.
    /// This only outputs the orchestration trace for demonstration purposes.
    /// To learn more about different traces available, see:
    /// https://docs.aws.amazon.com/bedrock/latest/userguide/trace-events.html
    /// </summary>
    private void OutputTrace(Trace trace)
    {
        if (trace.OrchestrationTrace is not null)
        {
            if (trace.OrchestrationTrace.ModelInvocationInput is not null)
            {
                this.Output.WriteLine("========== Orchestration trace ==========");
                this.Output.WriteLine("Orchestration input:");
                this.Output.WriteLine(trace.OrchestrationTrace.ModelInvocationInput.Text);
            }
            if (trace.OrchestrationTrace.ModelInvocationOutput is not null)
            {
                this.Output.WriteLine("========== Orchestration trace ==========");
                this.Output.WriteLine("Orchestration output:");
                this.Output.WriteLine(trace.OrchestrationTrace.ModelInvocationOutput.RawResponse.Content);
                this.Output.WriteLine("Usage:");
                this.Output.WriteLine($"Input token: {trace.OrchestrationTrace.ModelInvocationOutput.Metadata.Usage.InputTokens}");
                this.Output.WriteLine($"Output token: {trace.OrchestrationTrace.ModelInvocationOutput.Metadata.Usage.OutputTokens}");
            }
        }
        // Example output:
        // ========== Orchestration trace ==========
        // Orchestration input:
        // {"system":"You're a helpful assistant who helps users find information.You have been provided with a set of functions to answer ...
        // ========== Orchestration trace ==========
        // Orchestration output:
        // <thinking>
        // To answer this question, I will need to call the following functions:
        // 1. Step04_BedrockAgent_Trace_KernelFunctions::Current to get the current weather in Seattle
        // 2. Step04_BedrockAgent_Trace_KernelFunctions::Forecast to get the weather forecast in Seattle
        // </thinking>
        //
        // <function_calls>
        // <invoke>
        //     <tool_name>Step04_BedrockAgent_Trace_KernelFunctions::Current</tool_name>
        //     <parameters>
        //     <location>Seattle</location>
        //     </parameters>
        // Usage:
        // Input token: 617
        // Output token: 144
        // ========== Orchestration trace ==========
        // Orchestration input:
        // {"system":"You're a helpful assistant who helps users find information.You have been provided with a set of functions to answer ...
        // ========== Orchestration trace ==========
        // Orchestration output:
        // <thinking>Now that I have the current weather in Seattle, I will call the forecast function to get the weather forecast.</thinking>
        //
        // <function_calls>
        // <invoke>
        // <tool_name>Step04_BedrockAgent_Trace_KernelFunctions::Forecast</tool_name>
        // <parameters>
        // <location>Seattle</location>
        // </parameters>
        // Usage:
        // Input token: 834
        // Output token: 87
        // ========== Orchestration trace ==========
        // Orchestration input:
        // {"system":"You're a helpful assistant who helps users find information.You have been provided with a set of functions to answer ...
        // ========== Orchestration trace ==========
        // Orchestration output:
        // <answer>
        // The current weather in Seattle is 72 degrees. The weather forecast for Seattle is 75 degrees tomorrow.
        // Usage:
        // Input token: 1003
        // Output token: 31
    }
    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
        // Initialize kernel with plugins
        bedrockAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
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
