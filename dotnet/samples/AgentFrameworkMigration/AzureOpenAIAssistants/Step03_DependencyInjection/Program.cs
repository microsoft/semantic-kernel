// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using OpenAI.Assistants;

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
    serviceCollection.AddSingleton((sp) => new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential()).GetAssistantClient());
    serviceCollection.AddKernel().AddAzureOpenAIChatClient(deploymentName, endpoint, new AzureCliCredential());
    serviceCollection.AddTransient((sp) =>
    {
        var assistantsClient = sp.GetRequiredService<AssistantClient>();

        Assistant assistant = assistantsClient.CreateAssistant(deploymentName, new() { Name = "Joker", Instructions = "You are good at telling jokes." });

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

async Task AFAgent()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var serviceCollection = new ServiceCollection();
    serviceCollection.AddSingleton((sp) => new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential()).GetAssistantClient());
    serviceCollection.AddTransient((sp) =>
    {
        var assistantClient = sp.GetRequiredService<AssistantClient>();

        return assistantClient.CreateAIAgent(deploymentName, name: "Joker", instructions: "You are good at telling jokes.");
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
