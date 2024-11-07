#pragma warning disable SKEXP0070 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using System;

var builder = Kernel.CreateBuilder();
var modelId = "llama3.2";
var endpoint = new Uri("http://localhost:11434");

builder.Services.AddOllamaChatCompletion(modelId, endpoint);

builder.Plugins
    .AddFromType<MyTimePlugin>()
    .AddFromObject(new MyLightPlugin(turnedOn: true))
    .AddFromObject(new MyAlarmPlugin("11"));

var kernel = builder.Build();
var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

Console.WriteLine("Ask questions or give instructions to the copilot such as:\n" +
                    "- Change the alarm to 8\n" +
                    "- What is the current alarm set?\n" +
                    "- Is the light on?\n" +
                    "- Turn the light off please.\n" +
                    "- Set an alarm for 6:00 am.\n");

Console.Write("> ");

string? input = null;
while ((input = Console.ReadLine()) is not null)
{
    Console.WriteLine();

    try
    {
        ChatMessageContent chatResult = await chatCompletionService.GetChatMessageContentAsync(input, settings, kernel);
        Console.Write($"\n>>> Result: {chatResult}\n\n> ");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error: {ex.Message}\n\n> ");
    }
}
