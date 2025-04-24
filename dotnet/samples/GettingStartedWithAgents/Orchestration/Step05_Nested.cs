// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to nest an orchestration within another orchestration.
/// </summary>
public class Step05_Nested(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task NestConcurrentGroupsAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 =
            this.CreateAgent(
                instructions: "When the input is a number, N, respond with a number that is N + 1",
                description: "Increments the current value by +1");
        ChatCompletionAgent agent2 =
            this.CreateAgent(
                instructions: "When the input is a number, N, respond with a number that is N + 2",
                description: "Increments the current value by +2");
        ChatCompletionAgent agent3 =
            this.CreateAgent(
                instructions: "When the input is a number, N, respond with a number that is N + 3",
                description: "Increments the current value by +3");
        ChatCompletionAgent agent4 =
            this.CreateAgent(
                instructions: "When the input is a number, N, respond with a number that is N + 4",
                description: "Increments the current value by +4");

        // Define the pattern
        InProcessRuntime runtime = new();
        SequentialOrchestration<ConcurrentMessages.Request, ConcurrentMessages.Result> innerOrchestration =
            new(runtime, agent3, agent4)
            {
                InputTransform = (ConcurrentMessages.Request input) => ValueTask.FromResult(new SequentialMessage { Message = input.Message }),
                ResultTransform = (SequentialMessage result) => ValueTask.FromResult(new ConcurrentMessages.Result { Message = result.Message })
            };
        ConcurrentOrchestration outerOrchestration = new(runtime, agent1, innerOrchestration, agent2) { LoggerFactory = this.LoggerFactory };

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
