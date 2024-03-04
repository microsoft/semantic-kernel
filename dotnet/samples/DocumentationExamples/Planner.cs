// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example demonstrates how to create native functions for AI to call as described at
/// https://learn.microsoft.com/semantic-kernel/agents/plugins/using-the-KernelFunction-decorator
/// </summary>
public class Planner : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        WriteLine("======== Planner ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        // <RunningNativeFunction>
        var builder = Kernel.CreateBuilder()
                            .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);
        builder.Services.AddLogging(c => c.AddDebug().SetMinimumLevel(LogLevel.Trace));
        builder.Plugins.AddFromType<MathSolver>();
        Kernel kernel = builder.Build();

        // Get chat completion service
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Create chat history
        ChatHistory history = new();

        // Start the conversation
        Write("User > ");
        string? userInput;
        while ((userInput = ReadLine()) != null)
        {
            // Get user input
            Write("User > ");
            history.AddUserMessage(userInput!);

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
                    Write("Assistant > ");
                    first = false;
                }
                Write(content.Content);
                fullMessage += content.Content;
            }
            WriteLine();

            // Add the message from the agent to the chat history
            history.AddAssistantMessage(fullMessage);

            // Get user input again
            Write("User > ");
        }
    }

    public Planner(ITestOutputHelper output) : base(output)
    {
    }
}
