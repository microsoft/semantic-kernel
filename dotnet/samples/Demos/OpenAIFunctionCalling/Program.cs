// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using OpenAIFunctionCalling.Plugins;

async Task DoLoop(ChatHistory history, IChatCompletionService chatCompletionService, OpenAIPromptExecutionSettings settings, Kernel kernel)
{
    while (true)
    {
        Console.Write("User > ");
        string userMessage = Console.ReadLine()!;
        if (userMessage == "exit" || userMessage == "quit")
        {
            break;
        }

        if (string.IsNullOrEmpty(userMessage))
        {
            continue;
        }

        history.AddUserMessage(userMessage);

        try
        {
            ChatMessageContent results = await chatCompletionService.GetChatMessageContentAsync(history, settings, kernel);
            Console.WriteLine($"Assistant > {results.Content}");
            history.AddAssistantMessage(results.Content!);
        }
        catch (Exception e)
        {
            Console.WriteLine(e.Message);
        }
    }
}

async Task DoDemo(ChatHistory history, IChatCompletionService chatCompletionService, OpenAIPromptExecutionSettings settings, Kernel kernel)
{
    string userMessage = "change the alarm to 8";
    Console.WriteLine($"User > {userMessage}");
    history.AddUserMessage(userMessage);
    ChatMessageContent results = await chatCompletionService.GetChatMessageContentAsync(history, settings, kernel);
    Console.WriteLine($"Assistant > {results.Content}");
    history.AddAssistantMessage(results.Content!);
}

IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("o4-mini-2025-04-16", new OpenAIClient("API_KEY"));
builder.Plugins
    .AddFromType<MyTimePlugin>()
    .AddFromObject(new MyLightPlugin(turnedOn: true))
    .AddFromObject(new MyAlarmPlugin("11"));

Kernel kernel = builder.Build();

ChatHistory history = [];
history.AddSystemMessage("""
                         You are a helpful assistant.
                         You are not restricted to using the provided plugins,
                         and you can use information from your training.
                         Please explain your reasoning with the response.
                         """);

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
OpenAIPromptExecutionSettings settings = new()
{
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
};

Console.WriteLine("""
                  Ask questions or give instructions to the copilot such as:
                  - change the alarm to 8
                  - what is the current alarm set?
                  - is the light on?
                  - turn the light off please
                  - set an alarm for 6:00 am
                  """);

await DoLoop(history, chatCompletionService, settings, kernel);
