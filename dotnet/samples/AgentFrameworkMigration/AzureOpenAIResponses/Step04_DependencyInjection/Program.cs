// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;

#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o";
var userInput = "Tell me a joke about a pirate.";

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await SKAgent_As_AFAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddTransient<Microsoft.SemanticKernel.Agents.Agent>((sp)
        => new OpenAIResponseAgent(new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName))
        {
            Name = "Joker",
            Instructions = "You are good at telling jokes.",
            StoreEnabled = true
        });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<Microsoft.SemanticKernel.Agents.Agent>();

    var result = await agent.InvokeAsync(userInput).FirstAsync();
    Console.WriteLine(result.Message);
}

async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddTransient<Microsoft.SemanticKernel.Agents.Agent>((sp)
        => new OpenAIResponseAgent(new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName))
        {
            Name = "Joker",
            Instructions = "You are good at telling jokes.",
            StoreEnabled = true
        });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var skAgent = serviceProvider.GetRequiredService<Microsoft.SemanticKernel.Agents.Agent>();

    var agent = (skAgent as OpenAIResponseAgent)!.AsAIAgent();

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddTransient<AIAgent>((sp) => new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName)
        .CreateAIAgent(name: "Joker", instructions: "You are good at telling jokes."));

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
