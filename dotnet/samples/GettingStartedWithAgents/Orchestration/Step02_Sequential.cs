// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="SequentialOrchestration"/>.
/// </summary>
public class Step02_Sequential(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task SequentialTaskAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 =
            this.CreateAgent(
                """
                You are a marketing analyst. Given a product description, identify:
                - Key features
                - Target audience
                - Unique selling points
                """,
                description: "A agent that extracts key concepts from a product description.");
        ChatCompletionAgent agent2 =
            this.CreateAgent(
                """
                You are a marketing copywriter. Given a block of text describing features, audience, and USPs,
                compose a compelling marketing copy (like a newsletter section) that highlights these points.
                Output should be short (around 150 words), output just the copy as a single text block.
                """,
                description: "An agent that writes a marketing copy based on the extracted concepts.");
        ChatCompletionAgent agent3 =
            this.CreateAgent(
                """
                You are an editor. Given the draft copy, correct grammar, improve clarity, ensure consistent tone,
                give format and make it polished. Output the final improved copy as a single text block.
                """,
                description: "An agent that formats and proofreads the marketing copy.");

        // Define the orchestration
        SequentialOrchestration orchestration = new(agent1, agent2, agent3) { LoggerFactory = this.LoggerFactory };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "An eco-friendly stainless steel water bottle that keeps drinks cold for 24 hours";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }
}
