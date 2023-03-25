// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatMessageGeneration;
using Microsoft.SemanticKernel.Configuration;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT API
 */

// ReSharper disable once InconsistentNaming
public static class Example17_ChatGPT
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== SK with ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your text completion backend
        kernel.Config.AddOpenAIChatGPT("chat", "gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion backend = kernel.GetService<IChatCompletion>();
        var chat = (OpenAIChatHistory)backend.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chat.AddUserMessage("Hi, I'm looking for book suggestions");

        // First bot message
        string reply = await backend.GenerateMessageAsync(chat, new ChatRequestSettings());
        chat.AddAssistantMessage(reply);

        // Second user message
        chat.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");

        // Second bot message
        reply = await backend.GenerateMessageAsync(chat, new ChatRequestSettings());
        chat.AddAssistantMessage(reply);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chat.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }
    }
}
