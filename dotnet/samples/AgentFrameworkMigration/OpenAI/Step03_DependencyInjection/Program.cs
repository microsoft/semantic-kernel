// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using OpenAI;

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-4o";
var userInput = "Tell me a joke about a pirate.";

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddKernel().AddOpenAIChatClient(model, apiKey);
    serviceCollection.AddTransient((sp) => new ChatCompletionAgent()
    {
        Kernel = sp.GetRequiredService<Kernel>(),
        Name = "Joker",
        Instructions = "You are good at telling jokes."
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<ChatCompletionAgent>();

    await foreach (var item in agent.InvokeAsync(userInput))
    {
        Console.WriteLine(item.Message);
    }
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddTransient<AIAgent>((sp) => new OpenAIClient(apiKey)
        .GetChatClient(model)
        .CreateAIAgent(name: "Joker", instructions: "You are good at telling jokes."));

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
