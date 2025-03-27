// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// %%%
/// </summary>
public class Step05_Multiuse(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseMultiplePatternsAsync()
    {
        // Define the agents
        // %%% STRUCTURED OUTPUT ???
        ChatCompletionAgent agent1 =
                new()
                {
                    Instructions = "Count the number of words in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nWords: <count>",
                    //Name = name,
                    Description = "Agent 1",
                    Kernel = this.CreateKernelWithChatCompletion(),
                };
        ChatCompletionAgent agent2 =
                new()
                {
                    Instructions = "Count the number of vowels in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nVowels: <count>",
                    //Name = name,
                    Description = "Agent 2",
                    Kernel = this.CreateKernelWithChatCompletion(),
                };
        ChatCompletionAgent agent3 =
                new()
                {
                    Instructions = "Count the number of consonants in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nConsonants: <count>",
                    //Name = name,
                    Description = "Agent 3",
                    Kernel = this.CreateKernelWithChatCompletion(),
                };

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration broadcast = new(runtime, BroadcastCompletedHandlerAsync, agent2, agent3);
        HandoffOrchestration handoff = new(runtime, HandoffCompletedHandlerAsync, agent1);

        // Start the runtime
        await runtime.StartAsync();
        await broadcast.StartAsync(new ChatMessageContent(AuthorRole.User, "The quick brown fox jumps over the lazy dog"));
        await handoff.StartAsync(new ChatMessageContent(AuthorRole.User, "The quick brown fox jumps over the lazy dog"));
        await runtime.RunUntilIdleAsync();

        Console.WriteLine($"BROADCAST ISCOMPLETE = {broadcast.IsComplete}");
        Console.WriteLine($"HANDOFF ISCOMPLETE = {handoff.IsComplete}");

        ValueTask BroadcastCompletedHandlerAsync(ChatMessageContent[] results)
        {
            Console.WriteLine("BROADCAST RESULT:");
            for (int index = 0; index < results.Length; ++index)
            {
                ChatMessageContent result = results[index];
                Console.WriteLine($"#{index}: {result}");
            }
            return ValueTask.CompletedTask;
        }

        ValueTask HandoffCompletedHandlerAsync(ChatMessageContent result)
        {
            Console.WriteLine($"HANDOFF RESULT: {result}");
            return ValueTask.CompletedTask;
        }
    }
}
