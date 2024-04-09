// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// This example shows how to use OpenAI's tool calling capability via the chat completions interface.
public class Example59_OpenAIFunctionCalling : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        // Create kernel.
        IKernelBuilder builder = Kernel.CreateBuilder();

        // We recommend the usage of OpenAI latest models for the best experience with tool calling.
        // i.e. gpt-3.5-turbo-1106 or gpt-4-1106-preview
        builder.AddOpenAIChatCompletion("gpt-3.5-turbo-1106", TestConfiguration.OpenAI.ApiKey);

        builder.Services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Trace));
        Kernel kernel = builder.Build();

        // Add a plugin with some helper functions we want to allow the model to utilize.
        kernel.ImportPluginFromFunctions("HelperFunctions", new[]
        {
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
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
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
        });

        WriteLine("======== Example 1: Use automated function calling with a non-streaming prompt ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
            WriteLine();
        }

        WriteLine("======== Example 2: Use automated function calling with a streaming prompt ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            await foreach (var update in kernel.InvokePromptStreamingAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)))
            {
                Write(update);
            }
            WriteLine();
        }

        WriteLine("======== Example 3: Use manual function calling with a non-streaming prompt ========");
        {
            var chat = kernel.GetRequiredService<IChatCompletionService>();

            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

            var chatHistory = new ChatHistory();
            chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

            while (true)
            {
                ChatMessageContent result = await chat.GetChatMessageContentAsync(chatHistory, settings, kernel);
                if (result.Content is not null)
                {
                    Write(result.Content);
                }

                IEnumerable<FunctionCallRequestContent> functionCalls = result.Items.OfType<FunctionCallRequestContent>(); // Getting list of function calls.
                if (!functionCalls.Any())
                {
                    break;
                }

                chatHistory.Add(result); // Adding LLM response containing function calls(requests) to chat history as it's required by LLMs.

                foreach (var functionCall in functionCalls)
                {
                    try
                    {
                        FunctionCallResultContent functionResult = await functionCall.InvokeAsync(kernel); // Executing each function.

                        chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { functionResult })); // Adding function result to chat history.
                    }
                    catch (Exception ex)
                    {
                        chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionCallResultContent(functionCall, ex) })); // Adding function result to chat history.
                        // Adding exception to chat history.
                        // or
                        //string message = "Error details that LLM can reason about.";
                        //chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionResultContent(functionCall, message) })); 
                    }
                }

                WriteLine();
            }
        }

        /* Uncomment this to try in a console chat loop.
        Console.WriteLine("======== Example 4: Use automated function calling with a streaming chat ========");
        {
            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
            var chat = kernel.GetRequiredService<IChatCompletionService>();
            var chatHistory = new ChatHistory();

            while (true)
            {
                Console.Write("Question (Type \"quit\" to leave): ");
                string question = Console.ReadLine() ?? string.Empty;
                if (question == "quit")
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
        }*/
    }

    public Example59_OpenAIFunctionCalling(ITestOutputHelper output) : base(output)
    {
    }
}
