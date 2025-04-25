// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Orchestration.Magentic;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
public class Step06_Magentic(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SimpleMagenticChatAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 = this.CreateAgent("Analyze the previous message to determine count of words.  ALWAYS report the count using numeric digits formatted as:\nWords: <digits>", description: "Provides the word count");
        ChatCompletionAgent agent2 = this.CreateAgent("Analyze the previous message to determine count of vowels.  ALWAYS report the count using numeric digits formatted as:\nVowels: <digits>", description: "Provides the vowel count");
        ChatCompletionAgent agent3 = this.CreateAgent("Analyze the previous message to determine count of onsonants.  ALWAYS report the count using numeric digits formatted as:\nConsonants: <digits>", description: "Provides the consonant count");

        // Define the pattern
        InProcessRuntime runtime = new();
        MagenticOrchestration orchestration = new(runtime, this.CreateKernelWithChatCompletion(), agent1, agent2, agent3) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();

        string input = "how many vowels in: quick brown fox jumps over the lazy dog";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(30));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }

    // %%% MORE SAMPLES - MAGENTIC

    [Fact]
    public async Task SingleActorAsync()
    {
        // Define the agents
        ChatCompletionAgent agent = this.CreateAgent("When the input is a number, N, respond with a number that is N + 1", "Add 1 to the given number.");

        // Define the pattern
        InProcessRuntime runtime = new();
        MagenticOrchestration orchestration = new(runtime, this.CreateKernelWithChatCompletion(), agent) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        await runtime.StartAsync();
        string input = "How much is 1 + 1 + 1?";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);

        string output = await result.GetValueAsync(TimeSpan.FromSeconds(30));
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
        MagenticOrchestration<ChatMessages.InputTask, ChatMessages.Result> orchestrationInner = new(runtime, this.CreateKernelWithChatCompletion(), agent)
        {
            InputTransform = (ChatMessages.InputTask input) => ValueTask.FromResult(input),
            ResultTransform = (ChatMessages.Result result) => ValueTask.FromResult(result),
        };
        MagenticOrchestration orchestrationOuter = new(runtime, this.CreateKernelWithChatCompletion(), orchestrationInner) { LoggerFactory = this.LoggerFactory };

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
