// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use cancel a <see cref="SequentialOrchestration"/> while its running.
/// </summary>
public class Step02a_SequentialCancellation(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SequentialCancelledAsync()
    {
        // Define the agents
        ChatCompletionAgent agent =
            this.CreateChatCompletionAgent(
                """
                If the input message is a number, return the number incremented by one.
                """,
                description: "A agent that increments numbers.");

        // Define the orchestration
        SequentialOrchestration orchestration = new(agent) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "42";
        Console.WriteLine($"\n# INPUT: {input}\n");

        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);

        result.Cancel();
        await Task.Delay(TimeSpan.FromSeconds(3));

        try
        {
            string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
            Console.WriteLine($"\n# RESULT: {text}");
        }
        catch
        {
            Console.WriteLine("\n# CANCELLED");
        }

        await runtime.RunUntilIdleAsync();
    }
}
