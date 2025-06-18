// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="ConcurrentOrchestration"/>
/// for executing multiple agents on the same task in parallel.
/// </summary>
public class Step01_Concurrent(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ConcurrentTaskAsync(bool streamedResponse)
    {
        // Define the agents
        ChatCompletionAgent physicist =
            this.CreateAgent(
                instructions: "You are an expert in physics. You answer questions from a physics perspective.",
                name: "Physicist",
                description: "An expert in physics");
        ChatCompletionAgent chemist =
            this.CreateAgent(
                instructions: "You are an expert in chemistry. You answer questions from a chemistry perspective.",
                name: "Chemist",
                description: "An expert in chemistry");

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();

        // Define the orchestration
        ConcurrentOrchestration orchestration =
            new(physicist, chemist)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
                StreamingResponseCallback = streamedResponse ? monitor.StreamingResultCallback : null,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "What is temperature?";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestration.InvokeAsync(input, runtime);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n\n", output.Select(text => $"{text}"))}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }
}
