// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using OpenAI;

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-4o";
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
    var builder = Kernel.CreateBuilder().AddOpenAIChatClient(model, apiKey);

    ChatCompletionAgent agent = new()
    {
        Instructions = "You are a helpful assistant",
        Kernel = builder.Build(),
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };

    // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
    agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("KernelPluginName", [KernelFunctionFactory.CreateFromMethod(GetWeather)]));

    Console.WriteLine("\n=== SK Agent Response ===\n");

    await foreach (var item in agent.InvokeAsync(userInput))
    {
        Console.Write(item.Message);
    }
}

async Task AFAgentAsync()
{
    var agent = new OpenAIClient(apiKey).GetChatClient(model).CreateAIAgent(
        instructions: "You are a helpful assistant",
        tools: [AIFunctionFactory.Create(GetWeather)]);

    Console.WriteLine("\n=== AF Agent Response ===\n");

    var result = await agent.RunAsync(userInput);
    Console.WriteLine(result);
}
