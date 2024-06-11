// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionCalling;

/// <summary>
/// These examples demonstrate two ways functions called by the OpenAI LLM can be invoked using the SK streaming and non-streaming AI API:
///
/// 1. Automatic Invocation by SK:
///    Functions called by the LLM are invoked automatically by SK. The results of these function invocations
///    are automatically added to the chat history and returned to the LLM. The LLM reasons about the chat history
///    and generates the final response.
///    This approach is fully automated and requires no manual intervention from the caller.
///
/// 2. Manual Invocation by a Caller:
///    Functions called by the LLM are returned to the AI API caller. The caller controls the invocation phase where
///    they may decide which function to call, when to call them, how to handle exceptions, etc. The caller then
///    adds the function results or exceptions to the chat history and returns it to the LLM, which reasons about it
///    and generates the final response.
///    This approach is more manual and requires more manual intervention from the caller.
/// </summary>
public class OpenAI_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates auto function calling with a non-streaming prompt.
    /// </summary>
    [Fact]
    public async Task RunNonStreamingPromptWithAutoFunctionCallingAsync()
    {
        Console.WriteLine("Auto function calling with a non-streaming prompt.");

        Kernel kernel = CreateKernel();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        Console.WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
    }

    /// <summary>
    /// This example demonstrates auto function calling with a streaming prompt.
    /// </summary>
    [Fact]
    public async Task RunStreamingPromptAutoFunctionCallingAsync()
    {
        Console.WriteLine("Auto function calling with a streaming prompt.");

        Kernel kernel = CreateKernel();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        await foreach (StreamingKernelContent update in kernel.InvokePromptStreamingAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)))
        {
            Console.Write(update);
        }
    }

    /// <summary>
    /// This example demonstrates manual function calling with a non-streaming prompt.
    /// </summary>
    [Fact]
    public async Task RunNonStreamingPromptWithManualFunctionCallingAsync()
    {
        Console.WriteLine("Manual function calling with a non-streaming prompt.");

        Kernel kernel = CreateKernel();

        IChatCompletionService chat = kernel.GetRequiredService<IChatCompletionService>();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        ChatHistory chatHistory = new();
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

            foreach (FunctionCallContent functionCall in functionCalls)
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

    /// <summary>
    /// This example demonstrates how a simulated function can be added to the chat history using a manual function calling approach.
    /// </summary>
    /// <remarks>
    /// Simulated functions are not called or requested by the LLM but are added to the chat history by the caller.
    /// Simulated functions provide a way for callers to add additional information that, if provided via the prompt, would be ignored due to LLM training.
    /// </remarks>
    [Fact]
    public async Task RunNonStreamingPromptWithSimulatedFunctionAsync()
    {
        Console.WriteLine("Simulated function calling with a non-streaming prompt.");

        Kernel kernel = CreateKernel();

        IChatCompletionService chat = kernel.GetRequiredService<IChatCompletionService>();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        ChatHistory chatHistory = new();
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

            foreach (FunctionCallContent functionCall in functionCalls)
            {
                FunctionResultContent resultContent = await functionCall.InvokeAsync(kernel); // Executing each function.

                chatHistory.Add(resultContent.ToChatMessage());
            }

            // Adding a simulated function call to the connector response message
            FunctionCallContent simulatedFunctionCall = new("weather-alert", id: "call_123");
            result.Items.Add(simulatedFunctionCall);

            // Adding a simulated function result to chat history
            string simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
            chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

            Console.WriteLine();
        }
    }

    /// <summary>
    /// This example demonstrates a console chat with content streaming capabilities that uses auto function calling.
    /// </summary>
    [Fact]
    public async Task RunStreamingChatWithAutoFunctionCallingAsync()
    {
        Console.WriteLine("Auto function calling with a streaming chat");

        Kernel kernel = CreateKernel();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        IChatCompletionService chat = kernel.GetRequiredService<IChatCompletionService>();
        ChatHistory chatHistory = new();
        int iteration = 0;

        while (true)
        {
            Console.Write("Question (Type \"quit\" to leave): ");

            //string question = System.Console.ReadLine() ?? string.Empty;

            // Comment out this line and uncomment the one above to run in a console chat loop.
            string question = iteration == 0 ? "Given the current time of day and weather, what is the likely color of the sky in Boston?" : "quit";

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
            iteration++;
        }
    }

    private static Kernel CreateKernel()
    {
        // Create kernel
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
                }, "GetWeatherForCity", "Gets the current weather for the specified city"),
        ]);

        return kernel;
    }
}
