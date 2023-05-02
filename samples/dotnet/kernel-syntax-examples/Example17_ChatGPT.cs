// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT API
 */

// ReSharper disable once InconsistentNaming
// ReSharper disable CommentTypo
public static class Example17_ChatGPT
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== SK with ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
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

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chatHistory.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }

        /* Output:

        Chat content:
        ------------------------
        system: You are a librarian, expert about books
        ------------------------
        user: Hi, I'm looking for book suggestions
        ------------------------
        assistant: Sure, I'd be happy to help! What kind of books are you interested in? Fiction or non-fiction? Any particular genre?
        ------------------------
        user: I love history and philosophy, I'd like to learn something new about Greece, any suggestion?
        ------------------------
        assistant: Great! For history and philosophy books about Greece, here are a few suggestions:

        1. "The Greeks" by H.D.F. Kitto - This is a classic book that provides an overview of ancient Greek history and culture, including their philosophy, literature, and art.

        2. "The Republic" by Plato - This is one of the most famous works of philosophy in the Western world, and it explores the nature of justice and the ideal society.

        3. "The Peloponnesian War" by Thucydides - This is a detailed account of the war between Athens and Sparta in the 5th century BCE, and it provides insight into the political and military strategies of the time.

        4. "The Iliad" by Homer - This epic poem tells the story of the Trojan War and is considered one of the greatest works of literature in the Western canon.

        5. "The Histories" by Herodotus - This is a comprehensive account of the Persian Wars and provides a wealth of information about ancient Greek culture and society.

        I hope these suggestions are helpful!
        ------------------------
        */
    }
}
