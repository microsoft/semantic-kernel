// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using OpenAI.Assistants;

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
    serviceCollection.AddSingleton((sp) => new AssistantClient(apiKey));
    serviceCollection.AddKernel().AddOpenAIChatClient(model, apiKey);
    serviceCollection.AddTransient((sp) =>
    {
        var assistantsClient = sp.GetRequiredService<AssistantClient>();

        Assistant assistant = assistantsClient.CreateAssistant(model, new() { Name = "Joker", Instructions = "You are good at telling jokes." });

        return new OpenAIAssistantAgent(assistant, assistantsClient);
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<OpenAIAssistantAgent>();

    // Create a thread for the agent conversation.
    var assistantsClient = serviceProvider.GetRequiredService<AssistantClient>();
    var thread = new OpenAIAssistantAgentThread(assistantsClient);
    var settings = new OpenAIPromptExecutionSettings() { MaxTokens = 1000 };
    var agentOptions = new OpenAIAssistantAgentInvokeOptions() { KernelArguments = new(settings) };

    await foreach (var result in agent.InvokeAsync(userInput, thread, agentOptions))
    {
        Console.WriteLine(result.Message);
    }

    Console.WriteLine("---");
    await foreach (var update in agent.InvokeStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update.Message);
    }

    // Clean up
    await thread.DeleteAsync();
    await assistantsClient.DeleteAssistantAsync(agent.Id);
}

async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddSingleton((sp) => new AssistantClient(apiKey));
    serviceCollection.AddKernel().AddOpenAIChatClient(model, apiKey);
    serviceCollection.AddTransient((sp) =>
    {
        var assistantsClient = sp.GetRequiredService<AssistantClient>();

        Assistant assistant = assistantsClient.CreateAssistant(model, new() { Name = "Joker", Instructions = "You are good at telling jokes." });

        return new OpenAIAssistantAgent(assistant, assistantsClient);
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var skAgent = serviceProvider.GetRequiredService<OpenAIAssistantAgent>();

    var agent = skAgent.AsAIAgent();

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
    var assistantClient = serviceProvider.GetRequiredService<AssistantClient>();
    if (thread is ChatClientAgentThread chatThread)
    {
        await assistantClient.DeleteThreadAsync(chatThread.ConversationId);
    }
    await assistantClient.DeleteAssistantAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddSingleton((sp) => new AssistantClient(apiKey));
    serviceCollection.AddTransient((sp) =>
    {
        var assistantClient = sp.GetRequiredService<AssistantClient>();

        return assistantClient.CreateAIAgent(model, name: "Joker", instructions: "You are good at telling jokes.");
    });

    await using ServiceProvider serviceProvider = serviceCollection.BuildServiceProvider();
    var agent = serviceProvider.GetRequiredService<AIAgent>();

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
    var assistantClient = serviceProvider.GetRequiredService<AssistantClient>();
    if (thread is ChatClientAgentThread chatThread)
    {
        await assistantClient.DeleteThreadAsync(chatThread.ConversationId);
    }
    await assistantClient.DeleteAssistantAsync(agent.Id);
}
