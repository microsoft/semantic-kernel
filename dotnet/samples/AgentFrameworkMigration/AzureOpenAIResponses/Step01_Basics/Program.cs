// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
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

    var responseClient = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName);
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
        thread = item.Thread;
        Console.WriteLine(item.Message);
    }

    Console.WriteLine("---");
    await foreach (var item in agent.InvokeStreamingAsync(userInput, thread, agentOptions))
    {
        thread = item.Thread;
        Console.Write(item.Message);
    }
}

async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var responseClient = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName);

    OpenAIResponseAgent skAgent = new(responseClient)
    {
        Name = "Joker",
        Instructions = "You are good at telling jokes.",
        StoreEnabled = true
    };

    var agent = skAgent.AsAIAgent();

    var thread = agent.GetNewThread();
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

    var agent = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetResponsesClient(deploymentName)
        .CreateAIAgent(name: "Joker", instructions: "You are good at telling jokes.");

    var thread = agent.GetNewThread();
    var agentOptions = new ChatClientAgentRunOptions(new() { MaxOutputTokens = 8000 });

    var result = await agent.RunAsync(userInput, thread, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update);
    }
}
