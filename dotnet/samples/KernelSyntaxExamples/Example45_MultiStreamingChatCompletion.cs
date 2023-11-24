// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example45_MultiStreamingChatCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiStreamingChatCompletionAsync();
        await OpenAIMultiStreamingChatCompletionAsync();
    }

    private static async Task AzureOpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion - Raw Streaming ========");

        AzureOpenAIChatCompletion azureOpenAIChatCompletion = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await StreamingChatCompletionAsync(azureOpenAIChatCompletion);
    }

    private static async Task OpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion - Raw Streaming ========");

        OpenAIChatCompletion openAIChatCompletion = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        await StreamingChatCompletionAsync(openAIChatCompletion);
    }

    private static async Task StreamingChatCompletionAsync(IChatCompletion chatCompletion)
    {
        var requestSettings = new OpenAIRequestSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 3
        };

        var consoleLinesPerResult = 10;

        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for 5 random title names for sci-fi books");
        await MessageOutputAsync(chatHistory);

        PrepareDisplay();

        await foreach (var chatUpdate in chatCompletion.GetStreamingContentAsync<StreamingChatContent>("Hi, I'm looking for 5 random title names for sci-fi books", requestSettings))
        {
            Console.SetCursorPosition(0, chatUpdate.ChoiceIndex * consoleLinesPerResult);
            if (chatUpdate.Role.HasValue)
            {
                Console.Write($"Role: {chatUpdate.Role.Value}\n");
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine();

        Console.SetCursorPosition(0, requestSettings.ResultsPerPrompt * consoleLinesPerResult);
        Console.WriteLine();
    }

    /// <summary>
    /// Break enough lines as the current console window size to display the results
    /// </summary>
    private static void PrepareDisplay()
    {
        for (int i = 0; i < Console.WindowHeight - 2; i++)
        {
            Console.WriteLine();
        }
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }
}
