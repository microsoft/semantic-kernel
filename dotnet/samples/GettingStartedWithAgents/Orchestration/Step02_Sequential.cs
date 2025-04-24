// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="SequentialOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step02_Sequential(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SimpleSequentialAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 =
            this.CreateAgent(
                instructions:
                """                
                Analyze the previous message to determine count of words.

                ALWAYS report the count using numeric digits formatted as: Words: <digits>                
                """,
                description: "Able to count the number of words in a message");
        ChatCompletionAgent agent2 =
            this.CreateAgent(
                instructions:
                """                
                Analyze the previous message to determine count of vowels.

                ALWAYS report the count using numeric digits formatted as: Vowels: <digits>                
                """,
                description: "Able to count the number of vowels in a message");
        ChatCompletionAgent agent3 =
            this.CreateAgent(
                instructions:
                """                
                Analyze the previous message to determine count of consonants.

                ALWAYS report the count using numeric digits formatted as: Consonants: <digits>                
                """,
                description: "Able to count the number of consonants in a message");

        // Define the pattern
        InProcessRuntime runtime = new();
        SequentialOrchestration orchestration = new(runtime, agent1, agent2, agent3) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();
        string input = "The quick brown fox jumps over the lazy dog";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }
}
