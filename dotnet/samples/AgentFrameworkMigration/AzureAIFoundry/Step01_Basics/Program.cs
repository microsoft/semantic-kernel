// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

var azureEndpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT") ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME") ?? "gpt-4o";
var userInput = "Tell me a joke about a pirate.";

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var azureAgentClient = AzureAIAgent.CreateAgentsClient(azureEndpoint, new AzureCliCredential());

    PersistentAgent definition = await azureAgentClient.Administration.CreateAgentAsync(
        deploymentName,
        name: "GenerateStory",
        instructions: "You are good at telling jokes.");

    AzureAIAgent agent = new(definition, azureAgentClient);

    var thread = new AzureAIAgentThread(azureAgentClient);

    AzureAIAgentInvokeOptions options = new() { MaxPromptTokens = 1000 };
    var result = await agent.InvokeAsync(userInput, thread, options).FirstAsync();
    Console.WriteLine(result.Message);

    Console.WriteLine("---");
    await foreach (StreamingChatMessageContent update in agent.InvokeStreamingAsync(userInput, thread))
    {
        Console.Write(update);
    }

    // Clean up
    await thread.DeleteAsync();
    await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var azureAgentClient = new PersistentAgentsClient(azureEndpoint, new AzureCliCredential());

    var agent = await azureAgentClient.CreateAIAgentAsync(
        deploymentName,
        name: "GenerateStory",
        instructions: "You are good at telling jokes.");

    var thread = agent.GetNewThread();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 1000 });

    var result = await agent.RunAsync(userInput, thread, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update);
    }

    // Clean up
    if (thread is ChatClientAgentThread chatThread)
    {
        await azureAgentClient.Threads.DeleteThreadAsync(chatThread.ConversationId);
    }
    await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
}
