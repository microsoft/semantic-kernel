// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT API
 */
// ReSharper disable once InconsistentNaming
public static class Example49_LogitBias
{
    public static async Task RunAsync()
    {
        OpenAIChatCompletion chatCompletion = new("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        // Using the GPT Tokenizer: https://platform.openai.com/tokenizer
        // The following text is the tokenized version of the book related tokens
        // "novel literature reading author library story chapter paperback hardcover ebook publishing fiction nonfiction manuscript textbook bestseller bookstore reading list bookworm"

        // This will make the model try its best to avoid any of the above related words.
        var keys = new[] { 3919, 626, 17201, 1300, 25782, 9800, 32016, 13571, 43582, 20189, 1891, 10424, 9631, 16497, 12984, 20020, 24046, 13159, 805, 15817, 5239, 2070, 13466, 32932, 8095, 1351, 25323 };

        var settings = new ChatRequestSettings();
        foreach (var key in keys)
        {
            settings.TokenSelectionBiases.Add(key, -100);
        }

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = chatCompletion.CreateNewChat("You are a librarian expert");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking some suggestions");
        await MessageOutputAsync(chatHistory);

        string reply = await chatCompletion.GenerateMessageAsync(chatHistory, settings);
        chatHistory.AddAssistantMessage(reply);
        await MessageOutputAsync(chatHistory);

        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        await MessageOutputAsync(chatHistory);

        reply = await chatCompletion.GenerateMessageAsync(chatHistory, settings);
        chatHistory.AddAssistantMessage(reply);
        await MessageOutputAsync(chatHistory);

        /* Output:
        Chat content:
        ------------------------
        User: Hi, I'm looking some suggestions
        ------------------------
        Assistant: Sure, what kind of suggestions are you looking for?
        ------------------------
        User: I love history and philosophy, I'd like to learn something new about Greece, any suggestion?
        ------------------------
        Assistant: If you're interested in learning about ancient Greece, I would recommend the book "The Histories" by Herodotus. It's a fascinating account of the Persian Wars and provides a lot of insight into ancient Greek culture and society. For philosophy, you might enjoy reading the works of Plato, particularly "The Republic" and "The Symposium." These texts explore ideas about justice, morality, and the nature of love.
        ------------------------
        */
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
