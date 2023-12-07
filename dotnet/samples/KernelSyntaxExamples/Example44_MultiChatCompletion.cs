// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example44_MultiChatCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiChatCompletionAsync();
        await OpenAIMultiChatCompletionAsync();
    }

    private static async Task AzureOpenAIMultiChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion ========");

        AzureOpenAIChatCompletionService chatCompletionService = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.ChatModelId,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await RunChatAsync(chatCompletionService);
    }

    private static async Task OpenAIMultiChatCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion ========");

        OpenAIChatCompletionService chatCompletionService = new(modelId: TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        await RunChatAsync(chatCompletionService);
    }

    private static async Task RunChatAsync(IChatCompletionService chatCompletionService)
    {
        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");
        await MessageOutputAsync(chatHistory);

        var chatExecutionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0,
        };

        // First bot assistant message
        foreach (var chatMessageChoice in await chatCompletionService.GetChatMessageContentsAsync(chatHistory, chatExecutionSettings))
        {
            chatHistory.AddMessage(chatMessageChoice!);
            await MessageOutputAsync(chatHistory);
        }

        Console.WriteLine();
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
