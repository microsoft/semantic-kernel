// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using OpenAI.Assistants;
using OpenAI.Responses;

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

    var assistantsClient = new AssistantClient(apiKey);

    // Define the assistant
    Assistant assistant = await assistantsClient.CreateAssistantAsync(model, name: "Joker", instructions: "You are good at telling jokes.");

    // Create the agent
    OpenAIAssistantAgent agent = new(assistant, assistantsClient);

    // Create a thread for the agent conversation.
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

// Example of Semantic Kernel Agent code converted as an Agent Framework Agent
async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var assistantsClient = new AssistantClient(apiKey);

    // Define the assistant
    Assistant assistant = await assistantsClient.CreateAssistantAsync(model, name: "Joker", instructions: "You are good at telling jokes.");

    // Create the agent
    OpenAIAssistantAgent agent = new(assistant, assistantsClient);

    var afAgent = agent.AsAIAgent();

    var thread = await afAgent.CreateSessionAsync();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 1000 });

    var result = await afAgent.RunAsync(userInput, thread, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in afAgent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update);
    }

    // Clean up
    if (thread is ChatClientAgentSession chatSession)
    {
        await assistantsClient.DeleteThreadAsync(chatSession.ConversationId);
    }
    await assistantsClient.DeleteAssistantAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    // AF 1.0: OpenAI Assistants extensions (CreateAIAgentAsync/GetAIAgent) were removed.
    // OpenAI is deprecating the Assistants API in favor of the Responses API.
    // The recommended migration path is to use ResponsesClient.AsAIAgent() instead.
    var agent = new OpenAIClient(apiKey).GetResponsesClient()
        .AsAIAgent(model: model, name: "Joker", instructions: "You are good at telling jokes.");

    var session = await agent.CreateSessionAsync();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 1000 });

    var result = await agent.RunAsync(userInput, session, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, session, agentOptions))
    {
        Console.Write(update);
    }
}
