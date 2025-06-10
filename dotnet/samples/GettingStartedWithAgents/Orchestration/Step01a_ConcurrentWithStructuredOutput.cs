// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.Transforms;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="ConcurrentOrchestration"/> with structured output.
/// </summary>
public class Step01a_ConcurrentWithStructuredOutput(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    [Fact]
    public async Task ConcurrentStructuredOutputAsync()
    {
        // Define the agents
        ChatCompletionAgent agent1 =
            this.CreateAgent(
                instructions: "You are an expert in identifying themes in articles. Given an article, identify the main themes.",
                description: "An expert in identifying themes in articles");
        ChatCompletionAgent agent2 =
            this.CreateAgent(
                instructions: "You are an expert in sentiment analysis. Given an article, identify the sentiment.",
                description: "An expert in sentiment analysis");
        ChatCompletionAgent agent3 =
            this.CreateAgent(
                instructions: "You are an expert in entity recognition. Given an article, extract the entities.",
                description: "An expert in entity recognition");

        // Define the orchestration with transform
        Kernel kernel = this.CreateKernelWithChatCompletion();
        StructuredOutputTransform<Analysis> outputTransform =
            new(kernel.GetRequiredService<IChatCompletionService>(),
                new OpenAIPromptExecutionSettings { ResponseFormat = typeof(Analysis) });
        ConcurrentOrchestration<string, Analysis> orchestration =
            new(agent1, agent2, agent3)
            {
                LoggerFactory = this.LoggerFactory,
                ResultTransform = outputTransform.TransformAsync,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        const string resourceId = "Hamlet_full_play_summary.txt";
        string input = EmbeddedResource.Read(resourceId);
        Console.WriteLine($"\n# INPUT: @{resourceId}\n");
        OrchestrationResult<Analysis> result = await orchestration.InvokeAsync(input, runtime);

        Analysis output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 2));
        Console.WriteLine($"\n# RESULT:\n{JsonSerializer.Serialize(output, s_options)}");

        await runtime.RunUntilIdleAsync();
    }

    private sealed class Analysis
    {
        public IList<string> Themes { get; set; } = [];
        public IList<string> Sentiments { get; set; } = [];
        public IList<string> Entities { get; set; } = [];
    }
}
