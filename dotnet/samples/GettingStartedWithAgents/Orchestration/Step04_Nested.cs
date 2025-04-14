// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="SequentialOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step04_Nested(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task NestSequentialGroupsAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");
        ChatCompletionAgent agent2 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 2");
        ChatCompletionAgent agent3 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 3");
        ChatCompletionAgent agent4 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 4");

        // Define the pattern
        InProcessRuntime runtime = new();
        ConcurrentOrchestration<SequentialMessage, SequentialMessage> innerOrchestration =
            new(runtime, agent3, agent4)
            {
                InputTransform = (SequentialMessage input) => ValueTask.FromResult(new ConcurrentMessages.Request { Message = input.Content }),
                ResultTransform = (ConcurrentMessages.Result[] output) => ValueTask.FromResult(SequentialMessage.FromChat(new ChatMessageContent(AuthorRole.Assistant, string.Join("\n", output.Select(item => item.Message.Content)))))
            };
        SequentialOrchestration outerOrchestration = new(runtime, agent1, innerOrchestration, agent2);

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
    public async Task NestConcurrentGroupsAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");
        ChatCompletionAgent agent2 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 2");
        ChatCompletionAgent agent3 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 3");
        ChatCompletionAgent agent4 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 4");

        // Define the pattern
        InProcessRuntime runtime = new();
        SequentialOrchestration<ConcurrentMessages.Request, ConcurrentMessages.Result> innerOrchestration =
            new(runtime, agent3, agent4)
            {
                InputTransform = (ConcurrentMessages.Request input) => ValueTask.FromResult(new SequentialMessage { Content = input.Message }),
                ResultTransform = (SequentialMessage result) => ValueTask.FromResult(new ConcurrentMessages.Result { Message = result.Content })
            };
        ConcurrentOrchestration outerOrchestration = new(runtime, agent1, innerOrchestration, agent2);

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
