// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

/**
 * This example shows how to use OpenAI's tool calling capability via the chat completions interface.
 */
public static class Example59_OpenAIFunctionCalling
{
    public static async Task RunAsync()
    {
        // Create kernel.
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        builder.Services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Trace));
        Kernel kernel = builder.Build();

        // Add a plugin with some helper functions we want to allow the model to utilize.
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("HelperFunctions", new[]
        {
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime"),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "GetWeatherForCity", "Gets the current weather for the specified city"),
        }));

        Console.WriteLine("======== Example 1: Use automated function calling with a non-streaming prompt ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            Console.WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
            Console.WriteLine();
        }

        Console.WriteLine("======== Example 2: Use automated function calling with a streaming prompt ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            await foreach (var update in kernel.InvokePromptStreamingAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)))
            {
                Console.Write(update);
            }
            Console.WriteLine();
        }

        Console.WriteLine("======== Example 3: Use manual function calling with a non-streaming prompt ========");
        {
            var chat = kernel.GetRequiredService<IChatCompletionService>();
            var chatHistory = new ChatHistory();

            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };
            chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");
            while (true)
            {
                var result = (OpenAIChatMessageContent)await chat.GetChatMessageContentAsync(chatHistory, settings, kernel);

                if (result.Content is not null)
                {
                    Console.Write(result.Content);
                }

                List<ChatCompletionsFunctionToolCall> toolCalls = result.ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();
                if (toolCalls.Count == 0)
                {
                    break;
                }

                chatHistory.Add(result);
                foreach (var toolCall in toolCalls)
                {
                    string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
                        JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
                        "Unable to find function. Please try again!";

                    chatHistory.Add(new ChatMessageContent(
                        AuthorRole.Tool,
                        content,
                        metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
                }
            }

            Console.WriteLine();
        }

        Console.WriteLine("======== Example 4: Use manual function calling with a streaming prompt ========");
        {
            var chat = kernel.GetRequiredService<IChatCompletionService>();
            var chatHistory = new ChatHistory();

            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };
            chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");
            while (true)
            {
                List<ChatCompletionsFunctionToolCall> calls = new();
                StringBuilder contents = new();
                await foreach (OpenAIStreamingChatMessageContent update in chat.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
                {
                    if (update.Content is not null)
                    {
                        Console.Write(update.Content);
                        contents.Append(update.Content);
                    }

                    if (update.ToolCallUpdate is ChatCompletionsFunctionToolCall toolCall)
                    {
                        if (toolCall.Id is not null &&
                            (calls.Count == 0 || calls[^1].Id != toolCall.Id))
                        {
                            calls.Add(toolCall);
                        }
                        else if (calls.Count > 0)
                        {
                            ChatCompletionsFunctionToolCall last = calls[^1];
                            last.Name ??= toolCall.Name;
                            last.Arguments += toolCall.Arguments;
                        }
                    }
                }

                if (calls.Count == 0)
                {
                    break;
                }

                chatHistory.Add(new ChatMessageContent(AuthorRole.Assistant, contents.ToString(), metadata: new Dictionary<string, object?>() { { OpenAIChatMessageContent.ToolCallsProperty, calls } }));
                foreach (ChatCompletionsFunctionToolCall toolCall in calls)
                {
                    string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
                        JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
                        "Unable to find function. Please try again!";

                    chatHistory.Add(new ChatMessageContent(
                        AuthorRole.Tool,
                        content,
                        metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
                }
            }

            Console.WriteLine();
        }

        Console.WriteLine("======== Example 5: Use automated function calling with a streaming chat ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            var chat = kernel.GetRequiredService<IChatCompletionService>();
            var chatHistory = new ChatHistory();

            while (true)
            {
                Console.Write("Question: ");
                string question = Console.ReadLine() ?? string.Empty;
                if (question == "done")
                {
                    break;
                }

                chatHistory.AddUserMessage(question);
                StringBuilder sb = new();
                await foreach (var update in chat.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
                {
                    if (update.Content is not null)
                    {
                        Console.Write(update.Content);
                        sb.Append(update.Content);
                    }
                }
                chatHistory.AddAssistantMessage(sb.ToString());
                Console.WriteLine();
            }
        }
    }
}
