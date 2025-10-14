// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o";
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
    OpenAIResponseAgent agent = new(new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetOpenAIResponseClient(deploymentName));

    // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
    agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("KernelPluginName", [KernelFunctionFactory.CreateFromMethod(GetWeather)]));

    Console.WriteLine("\n=== SK Agent Response ===\n");

    await foreach (ChatMessageContent responseItem in agent.InvokeAsync(userInput))
    {
        if (!string.IsNullOrWhiteSpace(responseItem.Content))
        {
            Console.WriteLine(responseItem);
        }
    }
}

async Task AFAgentAsync()
{
    var agent = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
        .GetOpenAIResponseClient(deploymentName)
        .CreateAIAgent(instructions: "You are a helpful assistant", tools: [AIFunctionFactory.Create(GetWeather)]);

    Console.WriteLine("\n=== AF Agent Response ===\n");

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
