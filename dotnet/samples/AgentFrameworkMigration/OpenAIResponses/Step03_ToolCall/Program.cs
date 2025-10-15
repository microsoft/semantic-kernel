// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;

#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-4o";
var userInput = "What is the weather like in Amsterdam?";

Console.WriteLine($"User Input: {userInput}");

[KernelFunction]
[Description("Get the weather for a given location.")]
static string GetWeather([Description("The location to get the weather for.")] string location)
    => $"The weather in {location} is cloudy with a high of 15°C.";

await SKAgentAsync();
await SKAgent_As_AFAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    var builder = Kernel.CreateBuilder().AddOpenAIChatClient(model, apiKey);

    OpenAIResponseAgent agent = new(new OpenAIClient(apiKey).GetOpenAIResponseClient(model)) { StoreEnabled = true };

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

async Task SKAgent_As_AFAgentAsync()
{
    var builder = Kernel.CreateBuilder().AddOpenAIChatClient(model, apiKey);

    OpenAIResponseAgent skAgent = new(new OpenAIClient(apiKey).GetOpenAIResponseClient(model)) { StoreEnabled = true };

    // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
    skAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("KernelPluginName", [KernelFunctionFactory.CreateFromMethod(GetWeather)]));

    var agent = skAgent.AsAIAgent();

    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}

async Task AFAgentAsync()
{
    var agent = new OpenAIClient(apiKey).GetOpenAIResponseClient(model).CreateAIAgent(
        instructions: "You are a helpful assistant",
        tools: [AIFunctionFactory.Create(GetWeather)]);

    Console.WriteLine("\n=== AF Agent Response ===\n");

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
