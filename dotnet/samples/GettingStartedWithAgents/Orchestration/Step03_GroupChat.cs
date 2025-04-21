// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step03_GroupChat(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SimpleGroupChatAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("Analyze the previous message to determine count of words.  ALWAYS report the count using numeric digits formatted as:\nWords: <digits>");
        ChatCompletionAgent agent2 = this.CreateAgent("Analyze the previous message to determine count of vowels.  ALWAYS report the count using numeric digits formatted as:\nVowels: <digits>");
        ChatCompletionAgent agent3 = this.CreateAgent("Analyze the previous message to determine count of onsonants.  ALWAYS report the count using numeric digits formatted as:\nConsonants: <digits>");

        // Define the pattern
        InProcessRuntime runtime = new();
        GroupChatOrchestration orchestration = new(runtime, agent1, agent2, agent3) { LoggerFactory = this.LoggerFactory };

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

    [Fact]
    public async Task SingleActorAsync()
    {
        // Define the agents
        ChatCompletionAgent agent = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");

        // Define the pattern
        InProcessRuntime runtime = new();
        GroupChatOrchestration orchestration = new(runtime, agent) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);

        string output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {output}");

        await runtime.RunUntilIdleAsync();
    }

    [Fact]
    public async Task SingleNestedActorAsync()
    {
        // Define the agents
        ChatCompletionAgent agent = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1");

        // Define the pattern
        InProcessRuntime runtime = new();
        GroupChatOrchestration<ChatMessages.InputTask, ChatMessages.Result> orchestrationInner = new(runtime, agent)
        {
            InputTransform = (ChatMessages.InputTask input) => ValueTask.FromResult(input),
            ResultTransform = (ChatMessages.Result result) => ValueTask.FromResult(result),
        };
        GroupChatOrchestration orchestrationOuter = new(runtime, orchestrationInner) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();
        string input = "1";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestrationOuter.InvokeAsync(input);

        string output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {output}");

        await runtime.RunUntilIdleAsync();
    }
}
