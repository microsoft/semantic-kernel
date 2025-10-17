// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;

#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-4o";
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
        => new OpenAIResponseAgent(new OpenAIClient(apiKey).GetOpenAIResponseClient(model))
        {
            Name = "Joker",
            Instructions = "You are good at telling jokes."
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
        => new OpenAIResponseAgent(new OpenAIClient(apiKey).GetOpenAIResponseClient(model))
        {
            Name = "Joker",
            Instructions = "You are good at telling jokes."
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
    serviceCollection.AddTransient((sp) => new OpenAIClient(apiKey)
        .GetOpenAIResponseClient(model)
        .CreateAIAgent(name: "Joker", instructions: "You are good at telling jokes."));

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
