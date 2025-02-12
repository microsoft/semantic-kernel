// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> and inspect the agent's thought process.
/// To learn more about different traces available, see:
/// https://docs.aws.amazon.com/bedrock/latest/userguide/trace-events.html
/// </summary>
public class Step04_BedrockAgent_Trace(ITestOutputHelper output) : Step03_BedrockAgent_Functions(output)
{
    /// <summary>
    /// Demonstrates how to inspect the thought process of a <see cref="BedrockAgent"/> by enabling trace.
    /// </summary>
    [Fact]
    public async Task UseAgentWithTraceAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step04_BedrockAgent_Trace");

        // Respond to user input
        var userQuery = "What is the current weather in Seattle and what is the weather forecast in Seattle?";
        try
        {
            // Customize the request for advanced scenarios
            InvokeAgentRequest invokeAgentRequest = new()
            {
                AgentAliasId = BedrockAgent.WorkingDraftAgentAlias,
                AgentId = bedrock_agent.Id,
                SessionId = BedrockAgent.CreateSessionId(),
                InputText = userQuery,
                // Enable trace to inspect the agent's thought process
                EnableTrace = true,
            };

            var responses = bedrock_agent.InvokeAsync(invokeAgentRequest, null, CancellationToken.None);
            await foreach (var response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
                else if (response.InnerContent is TracePart tracePart)
                {
                    this.OutputTrace(tracePart.Trace);
                }
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
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
    }
}
