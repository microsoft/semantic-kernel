// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using OpenAI.Assistants;

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-4o";
var userInput = "What is the weather like in Amsterdam?";

[KernelFunction]
[Description("Get the weather for a given location.")]
static string GetWeather([Description("The location to get the weather for.")] string location)
    => $"The weather in {location} is cloudy with a high of 15°C.";

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var builder = Kernel.CreateBuilder();
    var assistantsClient = new AssistantClient(apiKey);

    Assistant assistant = await assistantsClient.CreateAssistantAsync(model,
        instructions: "You are a helpful assistant");

    OpenAIAssistantAgent agent = new(assistant, assistantsClient)
    {
        Kernel = builder.Build(),
        Arguments = new KernelArguments(new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 1000,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }),
    };

    // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
    agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("KernelPluginName", [KernelFunctionFactory.CreateFromMethod(GetWeather)]));

    // Create a thread for the agent conversation.
    var thread = new OpenAIAssistantAgentThread(assistantsClient);

    await foreach (var result in agent.InvokeAsync(userInput, thread))
    {
        Console.WriteLine(result.Message);
    }

    Console.WriteLine("---");
    await foreach (var update in agent.InvokeStreamingAsync(userInput, thread))
    {
        Console.Write(update.Message);
    }

    // Clean up
    await thread.DeleteAsync();
    await assistantsClient.DeleteAssistantAsync(agent.Id);
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var assistantClient = new AssistantClient(apiKey);

    var agent = await assistantClient.CreateAIAgentAsync(model,
        instructions: "You are a helpful assistant",
        tools: [AIFunctionFactory.Create(GetWeather)]);

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
    if (thread is ChatClientAgentThread chatThread)
    {
        await assistantClient.DeleteThreadAsync(chatThread.ConversationId);
    }
    await assistantClient.DeleteAssistantAsync(agent.Id);
}
