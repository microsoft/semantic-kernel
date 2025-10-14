// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
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

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddSingleton((sp) => AzureAIAgent.CreateAgentsClient(azureEndpoint, new AzureCliCredential()));
    serviceCollection.AddTransient<AzureAIAgent>((sp) =>
    {
        var azureAgentClient = sp.GetRequiredService<PersistentAgentsClient>();

        Console.Write("Creating agent in the cloud...");

        PersistentAgent definition = azureAgentClient.Administration
            .CreateAgent(deploymentName,
                name: "GenerateStory",
                instructions: "You are good at telling jokes.");

        Console.Write("Done\n");

        return new(definition, azureAgentClient);
    });
    serviceCollection.AddKernel();

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AzureAIAgent>();

    var thread = new AzureAIAgentThread(agent.Client);

    var result = await agent.InvokeAsync(userInput).FirstAsync();
    Console.WriteLine(result.Message);

    Console.WriteLine("---");
    await foreach (ChatMessageContent update in agent.InvokeAsync(userInput, thread))
    {
        Console.Write(update);
    }

    // Clean up
    await thread.DeleteAsync();
    await agent.Client.Administration.DeleteAgentAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddSingleton((sp) => new PersistentAgentsClient(azureEndpoint, new AzureCliCredential()));
    serviceCollection.AddTransient<AIAgent>((sp) =>
    {
        var azureAgentClient = sp.GetRequiredService<PersistentAgentsClient>();

        return azureAgentClient.CreateAIAgent(
            deploymentName,
            name: "GenerateStory",
            instructions: "You are good at telling jokes.");
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

    var thread = agent.GetNewThread();

    var result = await agent.RunAsync(userInput, thread);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread))
    {
        Console.Write(update);
    }

    // Clean up
    var azureAgentClient = serviceProvider.GetRequiredService<PersistentAgentsClient>();
    if (thread is ChatClientAgentThread chatThread)
    {
        await azureAgentClient.Threads.DeleteThreadAsync(chatThread.ConversationId);
    }
    await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
}
