// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

var agentInstructions = "You are a translation assistant who only responds in {0}. Respond to any input by outputting the name of the input language and then translating the input to {0}.";

// This sample compares running sequential orchestrations using
// Semantic Kernel and the Agent Framework.
Console.WriteLine("=== Semantic Kernel Sequential Orchestration ===");
await SKSequentialOrchestration();

Console.WriteLine("\n=== Agent Framework Sequential Agent Workflow ===");
await AFSequentialAgentWorkflow();

# region SKSequentialOrchestration
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
async Task SKSequentialOrchestration()
{
    SequentialOrchestration orchestration = new([
        GetSKTranslationAgent("French"),
        GetSKTranslationAgent("Spanish"),
        GetSKTranslationAgent("English")])
    {
        StreamingResponseCallback = StreamingResultCallback,
    };

    InProcessRuntime runtime = new();
    await runtime.StartAsync();

    // Run the orchestration
    OrchestrationResult<string> result = await orchestration.InvokeAsync("Hello, world!", runtime);
    string text = await result.GetValueAsync(TimeSpan.FromSeconds(20));

    await runtime.RunUntilIdleAsync();
}
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

ChatCompletionAgent GetSKTranslationAgent(string targetLanguage)
{
    var kernel = Kernel.CreateBuilder().AddAzureOpenAIChatCompletion(deploymentName, endpoint, new AzureCliCredential()).Build();
    return new ChatCompletionAgent()
    {
        Kernel = kernel,
        Instructions = string.Format(agentInstructions, targetLanguage),
        Description = $"Agent that translates texts to {targetLanguage}",
        Name = $"SKTranslationAgent_{targetLanguage}"
    };
}

ValueTask StreamingResultCallback(StreamingChatMessageContent streamedResponse, bool isFinal)
{
    Console.Write(streamedResponse.Content);

    if (isFinal)
    {
        Console.WriteLine();
    }

    return ValueTask.CompletedTask;
}
# endregion

# region AFSequentialAgentWorkflow
async Task AFSequentialAgentWorkflow()
{
    var client = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential()).GetChatClient(deploymentName).AsIChatClient();
    var frenchAgent = GetAFTranslationAgent("French", client);
    var spanishAgent = GetAFTranslationAgent("Spanish", client);
    var englishAgent = GetAFTranslationAgent("English", client);
    var sequentialAgentWorkflow = AgentWorkflowBuilder.BuildSequential(
        [frenchAgent, spanishAgent, englishAgent]);

    await using StreamingRun run = await InProcessExecution.StreamAsync(sequentialAgentWorkflow, "Hello, world!");
    await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

    string? lastExecutorId = null;
    await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
    {
        if (evt is AgentRunUpdateEvent e)
        {
            if (string.IsNullOrEmpty(e.Update.Text))
            {
                continue;
            }

            if (e.ExecutorId != lastExecutorId)
            {
                lastExecutorId = e.ExecutorId;
                Console.WriteLine();
                Console.Write($"{e.Update.AuthorName}: ");
            }

            Console.Write(e.Update.Text);
        }
    }
}

ChatClientAgent GetAFTranslationAgent(string targetLanguage, IChatClient chatClient) =>
    new(chatClient, string.Format(agentInstructions, targetLanguage), name: $"AFTranslationAgent_{targetLanguage}");
# endregion
