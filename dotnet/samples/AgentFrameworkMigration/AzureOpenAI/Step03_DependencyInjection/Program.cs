// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o";
var userInput = "Tell me a joke about a pirate.";

Console.WriteLine($"User Input: {userInput}");

await SKAgent();
await AFAgent();

async Task SKAgent()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddKernel().AddAzureOpenAIChatClient(deploymentName, endpoint, new AzureCliCredential());
    serviceCollection.AddTransient((sp) => new ChatCompletionAgent()
    {
        Kernel = sp.GetRequiredService<Kernel>(),
        Name = "Joker",
        Instructions = "You are good at telling jokes."
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<ChatCompletionAgent>();

    var result = await agent.InvokeAsync(userInput).FirstAsync();
    Console.WriteLine(result.Message);
}

async Task AFAgent()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddTransient((sp) => new AzureOpenAIClient(new(endpoint), new AzureCliCredential())
        .GetChatClient(deploymentName)
        .CreateAIAgent(name: "Joker", instructions: "You are good at telling jokes."));

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
