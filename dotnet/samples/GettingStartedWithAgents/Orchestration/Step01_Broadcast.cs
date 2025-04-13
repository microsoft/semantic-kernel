// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime.InProcess;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="BroadcastOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step01_Broadcast(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SimpleBroadcastAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("Analyze the previous message to determine count of words.  ALWAYS report the count using numeric digits formatted as:\nWords: <digits>");
        ChatCompletionAgent agent2 = this.CreateAgent("Analyze the previous message to determine count of vowels.  ALWAYS report the count using numeric digits formatted as:\nVowels: <digits>");
        ChatCompletionAgent agent3 = this.CreateAgent("Analyze the previous message to determine count of onsonants.  ALWAYS report the count using numeric digits formatted as:\nConsonants: <digits>");

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration orchestration = new(runtime, agent1, agent2, agent3);

        // Start the runtime
        await runtime.StartAsync();
        string input = "The quick brown fox jumps over the lazy dog";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestration.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }

    [Fact]
    public async Task NestedBroadcastAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");
        ChatCompletionAgent agent2 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 2");
        ChatCompletionAgent agent3 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 3");
        ChatCompletionAgent agent4 = this.CreateAgent("When the input is a number, N, respond with a number that is N + 4");

        // Define the pattern
        InProcessRuntime runtime = new();

        BroadcastOrchestration<BroadcastMessages.Task, BroadcastMessages.Result> orchestrationLeft = CreateNested(runtime, agent1, agent2);
        BroadcastOrchestration<BroadcastMessages.Task, BroadcastMessages.Result> orchestrationRight = CreateNested(runtime, agent3, agent4);
        BroadcastOrchestration orchestrationMain = new(runtime, orchestrationLeft, orchestrationRight);

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestrationMain.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }

    [Fact]
    public async Task SingleActorAsync()
    {
        // Define the agents
        ChatCompletionAgent agent = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration orchestration = new(runtime, agent);

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestration.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }

    [Fact]
    public async Task SingleNestedActorAsync()
    {
        // Define the agents
        ChatCompletionAgent agent = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");

        // Define the pattern
        InProcessRuntime runtime = new();
        BroadcastOrchestration<BroadcastMessages.Task, BroadcastMessages.Result> orchestrationInner = CreateNested(runtime, agent);
        BroadcastOrchestration orchestrationOuter = new(runtime, orchestrationInner);

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestrationOuter.InvokeAsync(input);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n", output.Select(text => $"\t{text}"))}");

        await runtime.RunUntilIdleAsync();
    }

    private static BroadcastOrchestration<BroadcastMessages.Task, BroadcastMessages.Result> CreateNested(InProcessRuntime runtime, params OrchestrationTarget[] targets)
    {
        return new(runtime, targets)
        {
            InputTransform = (BroadcastMessages.Task input) => ValueTask.FromResult(input),
            ResultTransform = (BroadcastMessages.Result[] results) => ValueTask.FromResult(string.Join("\n", results.Select(result => $"{result.Message}")).ToBroadcastResult()),
        };
    }
}
