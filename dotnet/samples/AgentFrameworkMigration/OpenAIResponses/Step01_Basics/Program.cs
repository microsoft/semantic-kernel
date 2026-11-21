// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
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

    var responseClient = new OpenAIClient(apiKey).GetResponsesClient();
    OpenAIResponseAgent agent = new(responseClient)
    {
        Name = "Joker",
        Instructions = "You are good at telling jokes.",
        StoreEnabled = true
    };

    var agentOptions = new OpenAIResponseAgentInvokeOptions() { ResponseCreationOptions = new() { MaxOutputTokenCount = 1000 } };

    Microsoft.SemanticKernel.Agents.AgentThread? thread = null;
    await foreach (var item in agent.InvokeAsync(userInput, thread, agentOptions))
    {
        Console.WriteLine(item.Message);
        thread = item.Thread;
    }

    Console.WriteLine("---");
    await foreach (var item in agent.InvokeStreamingAsync(userInput, thread, agentOptions))
    {
        // Thread need to be updated for subsequent calls
        thread = item.Thread;
        Console.Write(item.Message);
    }
}

async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var responseClient = new OpenAIClient(apiKey).GetResponsesClient();

    OpenAIResponseAgent skAgent = new(responseClient)
    {
        Name = "Joker",
        Instructions = "You are good at telling jokes.",
        StoreEnabled = true
    };

    var agent = skAgent.AsAIAgent();

    var thread = await agent.CreateSessionAsync();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 8000 });

    var result = await agent.RunAsync(userInput, thread, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update);
    }
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var agent = new OpenAIClient(apiKey).GetResponsesClient()
        .AsAIAgent(model: model, name: "Joker", instructions: "You are good at telling jokes.");

    var session = await agent.CreateSessionAsync();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 8000 });

    var result = await agent.RunAsync(userInput, session, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, session, agentOptions))
    {
        Console.Write(update);
    }
}
