// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step03_GroupChat(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task UseGroupChatPatternAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("Analyze the previous message to determine count of words.  ALWAYS report the count using numeric digits formatted as:\nWords: <digits>");
        ChatCompletionAgent agent2 = this.CreateAgent("Analyze the previous message to determine count of vowels.  ALWAYS report the count using numeric digits formatted as:\nVowels: <digits>");
        ChatCompletionAgent agent3 = this.CreateAgent("Analyze the previous message to determine count of onsonants.  ALWAYS report the count using numeric digits formatted as:\nConsonants: <digits>");

        // Define the pattern
        InProcessRuntime runtime = new();
        GroupChatOrchestration orchestration = new(runtime, agent1, agent2, agent3);

        // Start the runtime
        await runtime.StartAsync();

        string input = "The quick brown fox jumps over the lazy dog";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }

    // %%% MORE SAMPLES - GROUPCHAT
}
