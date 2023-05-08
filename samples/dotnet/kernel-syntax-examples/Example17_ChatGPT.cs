// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT API
 */
// ReSharper disable once InconsistentNaming
public static class Example17_ChatGPT
{
    public static async Task RunAsync()
    {
        await AzureOpenAIChatStreamSampleAsync();
        await OpenAIChatStreamSampleAsync();

        await AzureOpenAIChatSampleAsync();
        await OpenAIChatSampleAsync();

        /* Output:

        Chat content:
        ------------------------
        System: You are a librarian, expert about books
        ------------------------
        User: Hi, I'm looking for book suggestions
        ------------------------
        Assistant: Sure, I'd be happy to help! What kind of books are you interested in? Fiction or non-fiction? Any particular genre?
        ------------------------
        User: I love history and philosophy, I'd like to learn something new about Greece, any suggestion?
        ------------------------
        Assistant: Great! For history and philosophy books about Greece, here are a few suggestions:

        1. "The Greeks" by H.D.F. Kitto - This is a classic book that provides an overview of ancient Greek history and culture, including their philosophy, literature, and art.

        2. "The Republic" by Plato - This is one of the most famous works of philosophy in the Western world, and it explores the nature of justice and the ideal society.

        3. "The Peloponnesian War" by Thucydides - This is a detailed account of the war between Athens and Sparta in the 5th century BCE, and it provides insight into the political and military strategies of the time.

        4. "The Iliad" by Homer - This epic poem tells the story of the Trojan War and is considered one of the greatest works of literature in the Western canon.

        5. "The Histories" by Herodotus - This is a comprehensive account of the Persian Wars and provides a wealth of information about ancient Greek culture and society.

        I hope these suggestions are helpful!
        ------------------------
        */
    }

    private static async Task OpenAIChatSampleAsync()
    {
        Console.WriteLine("======== Open AI - ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        await StartChatAsync(chatGPT);
    }

    private static async Task AzureOpenAIChatSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddAzureChatCompletionService(
            Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        await StartChatAsync(chatGPT);
    }

    private static async Task OpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Open AI - ChatGPT Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        await StartStreamingChatAsync(chatGPT);
    }

    private static async Task AzureOpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - ChatGPT Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddAzureChatCompletionService(
            Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        await StartStreamingChatAsync(chatGPT);
    }

    private static async Task StartStreamingChatAsync(IChatCompletion chatGPT)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = (OpenAIChatHistory)chatGPT.CreateNewChat("You are a librarian, expert about books");
        await UserMessageOutputAsync(chatHistory.Messages.Last());

        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        await UserMessageOutputAsync(chatHistory.Messages.Last());
        await AssistantMessageOutputAsync(chatGPT, chatHistory);

        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        await UserMessageOutputAsync(chatHistory.Messages.Last());
        await AssistantMessageOutputAsync(chatGPT, chatHistory);
    }

    private static async Task StartChatAsync(IChatCompletion chatGPT)
    {
        OpenAIChatHistory chatHistory = await PrepareChatHistoryAsync(chatGPT);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chatHistory.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }
    }

    private static Task UserMessageOutputAsync(ChatHistory.Message message)
    {
        Console.WriteLine($"{message.AuthorRole}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }

    private static async Task AssistantMessageOutputAsync(IChatCompletion chatGPT, OpenAIChatHistory chatHistory)
    {
        Console.Write("Assistant: ");
        string assistantMessage = string.Empty;
        await foreach (string message in chatGPT.GenerateMessageStreamAsync(chatHistory))
        {
            assistantMessage += message;
            Console.Write(message);
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddAssistantMessage(assistantMessage);
    }

    private static async Task<OpenAIChatHistory> PrepareChatHistoryAsync(IChatCompletion chatGPT)
    {
        var chatHistory = (OpenAIChatHistory)chatGPT.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");

        // First bot message
        string reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");

        // Second bot message
        reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);
        return chatHistory;
    }
}
