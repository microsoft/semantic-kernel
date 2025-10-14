// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

var azureEndpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT") ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME") ?? "gpt-4o";
var userInput = "What is the weather like in Amsterdam?";

Console.WriteLine($"User Input: {userInput}");

[KernelFunction]
[Description("Get the weather for a given location.")]
static string GetWeather([Description("The location to get the weather for.")] string location)
    => $"The weather in {location} is cloudy with a high of 15°C.";

await SKAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var azureAgentClient = AzureAIAgent.CreateAgentsClient(azureEndpoint, new AzureCliCredential());

    PersistentAgent definition = await azureAgentClient.Administration.CreateAgentAsync(deploymentName, instructions: "You are a helpful assistant");

    AzureAIAgent agent = new(definition, azureAgentClient)
    {
        Kernel = Kernel.CreateBuilder().Build(),
        Name = "Host",
        Instructions = "You are a helpful assistant",
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };

    var thread = new AzureAIAgentThread(azureAgentClient);

    // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
    agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("KernelPluginName", [KernelFunctionFactory.CreateFromMethod(GetWeather)]));

    var result = await agent.InvokeAsync(userInput).FirstAsync();
    Console.WriteLine(result.Message);

    Console.WriteLine("---");
    await foreach (ChatMessageContent update in agent.InvokeAsync(userInput, thread))
    {
        Console.Write(update);
    }

    // Clean up
    await thread.DeleteAsync();
    await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var azureAgentClient = new PersistentAgentsClient(azureEndpoint, new AzureCliCredential());

    var agent = await azureAgentClient.CreateAIAgentAsync(deploymentName, instructions: "Answer questions about the menu");

    var thread = agent.GetNewThread();
    var agentOptions = new ChatClientAgentRunOptions(new() { Tools = [AIFunctionFactory.Create(GetWeather)] });

    var result = await agent.RunAsync(userInput, thread, agentOptions);
    Console.WriteLine(result);

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        Console.Write(update);
    }

    // Clean up
    if (thread is ChatClientAgentThread chatThread)
    {
        await azureAgentClient.Threads.DeleteThreadAsync(chatThread.ConversationId);
    }
    await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
}
