// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="ConcurrentOrchestration"/>.
/// </summary>
public class Step01_Concurrent(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task ConcurrentTaskAsync()
    {
        // Define the agents
        ChatCompletionAgent physicist =
            this.CreateAgent(
                instructions: "You are an expert in physics. You answer questions from a physics perspective.",
                description: "An expert in physics");
        ChatCompletionAgent chemist =
            this.CreateAgent(
                instructions: "You are an expert in chemistry. You answer questions from a chemistry perspective.",
                description: "An expert in chemistry");

        // Define the orchestration
        OrchestrationMonitor monitor = new();
        ConcurrentOrchestration orchestration =
            new(physicist, chemist)
            {
                ResponseCallback = monitor.ResponseCallback,
                LoggerFactory = this.LoggerFactory
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "The quick brown fox jumps over the lazy dog";
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
