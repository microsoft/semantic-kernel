// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="HandoffOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step04_Nested(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task NestHandoffBroadcastAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");
        ChatCompletionAgent agent2 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 2");
        ChatCompletionAgent agent3 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 3");
        ChatCompletionAgent agent4 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 4");

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration<HandoffMessage, HandoffMessage> innerOrchestration =
            new(runtime, agent3, agent4)
            {
                InputTransform = (HandoffMessage input) => ValueTask.FromResult(new BroadcastMessages.Task { Message = input.Content }),
                ResultTransform = (BroadcastMessages.Result[] output) => ValueTask.FromResult(HandoffMessage.FromChat(new ChatMessageContent(AuthorRole.Assistant, string.Join("\n", output.Select(item => item.Message.Content)))))
            };
        HandoffOrchestration outerOrchestration = new(runtime, agent1, innerOrchestration, agent2);

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await outerOrchestration.InvokeAsync(input);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n> RESULT:\n{text}");

        await runtime.RunUntilIdleAsync();
    }

    [Fact]
    public async Task NestBroadcastHandoffAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");
        ChatCompletionAgent agent2 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 2");
        ChatCompletionAgent agent3 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 3");
        ChatCompletionAgent agent4 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 4");

        // Define the pattern
        InProcessRuntime runtime = new();
        HandoffOrchestration<BroadcastMessages.Task, BroadcastMessages.Result> innerOrchestration =
            new(runtime, agent3, agent4)
            {
                InputTransform = (BroadcastMessages.Task input) => ValueTask.FromResult(new HandoffMessage { Content = input.Message }),
                ResultTransform = (HandoffMessage result) => ValueTask.FromResult(new BroadcastMessages.Result { Message = result.Content })
            };
        BroadcastOrchestration outerOrchestration = new(runtime, agent1, innerOrchestration, agent2);

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await outerOrchestration.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n> RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }
}
