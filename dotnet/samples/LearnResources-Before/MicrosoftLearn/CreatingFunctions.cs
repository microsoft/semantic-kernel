// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Plugins;

namespace Examples;

/// <summary>
/// This example demonstrates how to create native functions for AI to call as described at
/// https://learn.microsoft.com/semantic-kernel/agents/plugins/using-the-KernelFunction-decorator
/// </summary>
public class CreatingFunctions(ITestOutputHelper output) : LearnBaseTest(["What is 49 diivided by 37?"], output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Creating native functions ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            Console.WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        // <RunningNativeFunction>
        var builder = Kernel.CreateBuilder()
                            .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);
        builder.Plugins.AddFromType<MathPlugin>();
        Kernel kernel = builder.Build();

        // Test the math plugin
        double answer = await kernel.InvokeAsync<double>(
            "MathPlugin", "Sqrt", new()
            {
                { "number1", 12 }
            });
        Console.WriteLine($"The square root of 12 is {answer}.");
        // </RunningNativeFunction>

        // Create chat history
        ChatHistory history = [];

        // <Chat>

        // Get chat completion service
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Start the conversation
        Console.Write("User > ");
        string? userInput;
        while ((userInput = Console.ReadLine()) is not null)
        {
            history.AddUserMessage(userInput);

            // Enable auto function calling
            OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
            };

            // Get the response from the AI
            var result = chatCompletionService.GetStreamingChatMessageContentsAsync(
                                history,
                                executionSettings: openAIPromptExecutionSettings,
                                kernel: kernel);

            // Stream the results
            string fullMessage = "";
            var first = true;
            await foreach (var content in result)
            {
                if (content.Role.HasValue && first)
                {
                    Console.Write("Assistant > ");
                    first = false;
                }
                Console.Write(content.Content);
                fullMessage += content.Content;
            }
            Console.WriteLine();

            // Add the message from the agent to the chat history
            history.AddAssistantMessage(fullMessage);

            // Get user input again
            Console.Write("User > ");
        }

        // </Chat>
    }
}
