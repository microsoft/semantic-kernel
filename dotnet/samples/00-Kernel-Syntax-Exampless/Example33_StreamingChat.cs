// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with streaming Chat Completion
 */
// ReSharper disable once InconsistentNaming
public static class Example33_StreamingChat
{
    public static async Task RunAsync()
    {
        await AzureOpenAIChatStreamSampleAsync();
        await OpenAIChatStreamSampleAsync();
    }

    private static async Task OpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Open AI - ChatGPT Streaming ========");

        OpenAIChatCompletion openAIChatCompletion = new(TestConfiguration.OpenAI.ChatCompletionModelId, TestConfiguration.OpenAI.ApiKey);

        await StartStreamingChatAsync(openAIChatCompletion);
    }

    private static async Task AzureOpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - ChatGPT Streaming ========");

        AzureChatCompletion azureChatCompletion = new(
           TestConfiguration.AzureOpenAI.ChatCompletionDeploymentName,
           TestConfiguration.AzureOpenAI.Endpoint,
           TestConfiguration.AzureOpenAI.ApiKey);

        await StartStreamingChatAsync(azureChatCompletion);
    }

    private static async Task StartStreamingChatAsync(IChatCompletion chatCompletion)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");
        await MessageOutputAsync(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        await MessageOutputAsync(chatHistory);

        // First bot assistant message
        await StreamMessageOutputAsync(chatCompletion, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        await MessageOutputAsync(chatHistory);

        // Second bot assistant message
        await StreamMessageOutputAsync(chatCompletion, chatHistory, AuthorRole.Assistant);
    }

    private static async Task StreamMessageOutputAsync(IChatCompletion chatGPT, ChatHistory chatHistory, AuthorRole authorRole)
    {
        Console.Write($"{authorRole}: ");
        string fullMessage = string.Empty;

        await foreach (string message in chatGPT.GenerateMessageStreamAsync(chatHistory))
        {
            fullMessage += message;
            Console.Write(message);
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Messages.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }
}
