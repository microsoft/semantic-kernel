// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// This example shows how to use the OpenAI connector with PZERO's OpenAI-compatible endpoint.
/// <list type="number">
/// <item>Get a key from https://pzero.studio/agents</item>
/// <item>Set the environment variable PZERO_API_KEY with your key</item>
/// <item>Configure the endpoint to https://api.pzero.studio/v1</item>
/// <item>Run the example</item>
/// </list>
/// </summary>
public class PZero_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example shows how to configure PZERO OpenAI-compatible endpoint with Kernel InvokeAsync.
    /// </summary>
    [Fact]
    public async Task UsingKernelWithPZero()
    {
        Console.WriteLine($"======== PZERO - Chat Completion - {nameof(UsingKernelWithPZero)} ========");

        var apiKey = Environment.GetEnvironmentVariable("PZERO_API_KEY");
        if (string.IsNullOrEmpty(apiKey))
        {
            Console.WriteLine("PZERO_API_KEY environment variable is not set. Skipping execution.");
            return;
        }

        var modelId = "deepseek-v4-flash";
        var endpoint = new Uri("https://api.pzero.studio/v1");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                endpoint: endpoint,
                apiKey: apiKey)
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business email. Use a professional tone, be clear and concise.
                   Sign the email as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            TopP = 0.5,
            MaxTokens = 1000,
        });

        var response = await kernel.InvokeAsync(mailFunction, new() { ["input"] = "Tell David that I will complete the report by Friday." });
        Console.WriteLine(response);
    }

    /// <summary>
    /// Sample showing how to use <see cref="IChatCompletionService"/> directly with a <see cref="ChatHistory"/> against PZERO.
    /// </summary>
    [Fact]
    public async Task UsingServiceNonStreamingWithPZero()
    {
        Console.WriteLine($"======== PZERO - Chat Completion - {nameof(UsingServiceNonStreamingWithPZero)} ========");

        var apiKey = Environment.GetEnvironmentVariable("PZERO_API_KEY");
        if (string.IsNullOrEmpty(apiKey))
        {
            Console.WriteLine("PZERO_API_KEY environment variable is not set. Skipping execution.");
            return;
        }

        var modelId = "deepseek-v4-flash";
        var endpoint = new Uri("https://api.pzero.studio/v1");

        OpenAIChatCompletionService chatService = new(modelId: modelId, endpoint: endpoint, apiKey: apiKey);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a helpful assistant.");

        chatHistory.AddUserMessage("Hello! Can you summarize the purpose of Semantic Kernel in one sentence?");
        this.OutputLastMessage(chatHistory);

        var reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        this.OutputLastMessage(chatHistory);
    }
}
