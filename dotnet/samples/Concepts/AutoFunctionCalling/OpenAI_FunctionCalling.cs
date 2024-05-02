// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace AutoFunctionCalling;

// This example shows how to use OpenAI's tool calling capability via the chat completions interface.
public class OpenAI_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
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
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
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
        ]);

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

            OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

            var chatHistory = new ChatHistory();
            chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

            while (true)
            {
                ChatMessageContent result = await chat.GetChatMessageContentAsync(chatHistory, settings, kernel);
                if (result.Content is not null)
                {
                    Console.Write(result.Content);
                }

                IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(result);
                if (!functionCalls.Any())
                {
                    break;
                }

                chatHistory.Add(result); // Adding LLM response containing function calls(requests) to chat history as it's required by LLMs.

                foreach (var functionCall in functionCalls)
                {
                    try
                    {
                        FunctionResultContent resultContent = await functionCall.InvokeAsync(kernel); // Executing each function.

                        chatHistory.Add(resultContent.ToChatMessage());
                    }
                    catch (Exception ex)
                    {
                        chatHistory.Add(new FunctionResultContent(functionCall, ex).ToChatMessage()); // Adding function result to chat history.
                        // Adding exception to chat history.
                        // or
                        //string message = "Error details that LLM can reason about.";
                        //chatHistory.Add(new FunctionResultContent(functionCall, message).ToChatMessageContent()); // Adding function result to chat history.
                    }
                }

                Console.WriteLine();
            }
        }

        Console.WriteLine("======== Example 4: Simulated function calling with a non-streaming prompt ========");
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
                    Console.Write(result.Content);
                }

                chatHistory.Add(result); // Adding LLM response containing function calls(requests) to chat history as it's required by LLMs.

                IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(result);
                if (!functionCalls.Any())
                {
                    break;
                }

                foreach (var functionCall in functionCalls)
                {
                    FunctionResultContent resultContent = await functionCall.InvokeAsync(kernel); // Executing each function.

                    chatHistory.Add(resultContent.ToChatMessage());
                }

                // Adding a simulated function call to the connector response message
                var simulatedFunctionCall = new FunctionCallContent("weather-alert", id: "call_123");
                result.Items.Add(simulatedFunctionCall);

                // Adding a simulated function result to chat history
                var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
                chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

                Console.WriteLine();
            }
        }

        /* Uncomment this to try in a console chat loop.
        Console.WriteLine("======== Example 5: Use automated function calling with a streaming chat ========");
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
}
