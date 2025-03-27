// Copyright (c) Microsoft. All rights reserved.
using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step01_Broadcast(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseBroadcastPatternAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 =
                new()
                {
                    Instructions = "",
                    //Name = name,
                    Description = "Agent 1",
                    Kernel = this.CreateKernelWithChatCompletion(),
                };
        ChatCompletionAgent agent2 =
                new()
                {
                    Instructions = "",
                    //Name = name,
                    Description = "Agent 2",
                    Kernel = this.CreateKernelWithChatCompletion(),
                };

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration orchestration = new(runtime, BroadcastCompletedHandlerAsync, agent1, agent2);

        // Start the runtime
        await runtime.StartAsync();
        await orchestration.StartAsync(new ChatMessageContent(AuthorRole.User, "// %%%"));
        await runtime.RunUntilIdleAsync();

        //Console.WriteLine(orchestration.Result);

        ValueTask BroadcastCompletedHandlerAsync(BroadcastMessages.Result[] results)
        {
            Console.WriteLine("RESULT:");
            for (int index = 0; index < results.Length; ++index)
            {
                BroadcastMessages.Result result = results[index];
                Console.WriteLine($"#{index}: {result.Message}");
            }
            return ValueTask.CompletedTask;
        }
    }
}
