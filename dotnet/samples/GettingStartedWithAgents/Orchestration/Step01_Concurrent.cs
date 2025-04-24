// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step01_Concurrent(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SimpleConcurrentAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("Analyze the previous message to determine count of words.  ALWAYS report the count using numeric digits formatted as:\nWords: <digits>");
        ChatCompletionAgent agent2 = this.CreateAgent("Analyze the previous message to determine count of vowels.  ALWAYS report the count using numeric digits formatted as:\nVowels: <digits>");
        ChatCompletionAgent agent3 = this.CreateAgent("Analyze the previous message to determine count of consonants.  ALWAYS report the count using numeric digits formatted as:\nConsonants: <digits>");

        // Define the pattern
        InProcessRuntime runtime = new();
        ConcurrentOrchestration orchestration = new(runtime, agent1, agent2, agent3) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();
        string input = "The quick brown fox jumps over the lazy dog";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestration.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }
}
