// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
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
        await AzureOpenAIChatStreamSampleAsync();
        await OpenAIChatStreamSampleAsync();
        await CustomChatStreamSampleAsync();

        await AzureOpenAIChatSampleAsync();
        await OpenAIChatSampleAsync();
        await CustomChatSampleAsync();
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
        Console.WriteLine("======== SK with ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
        OpenAIChatHistory chatHistory = await PrepareChatHistoryAsync(chatGPT);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chatHistory.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }
    }

    private static async Task AzureOpenAIChatSampleAsync()
    {
        Console.WriteLine("======== SK with ChatGPT ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddAzureChatCompletionService(
            Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
        OpenAIChatHistory chatHistory = await PrepareChatHistoryAsync(chatGPT);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chatHistory.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }
    }

    private static async Task OpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Open AI ChatGPT - Stream ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        await foreach (var message in StreamingChatAsync(chatGPT))
        {
            Console.Write(message);
        }
    }

    private static async Task AzureOpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI ChatGPT - Stream ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your chat completion service
        kernel.Config.AddAzureChatCompletionService(
            Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        await foreach (var message in StreamingChatAsync(chatGPT))
        {
            Console.Write(message);
        }
    }

    private static async IAsyncEnumerable<string> StreamingChatAsync(IChatCompletion chatGPT)
    {
        var chatHistory = (OpenAIChatHistory)chatGPT.CreateNewChat("You are a librarian, expert about books");
        yield return MessageToString(chatHistory.Messages.Last());

        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        yield return MessageToString(chatHistory.Messages.Last());

        await foreach (var assistantWord in AssistantStreamMessageAsync(chatGPT, chatHistory))
        {
            yield return assistantWord;
        }

        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        yield return MessageToString(chatHistory.Messages.Last());

        await foreach (var assistantWord in AssistantStreamMessageAsync(chatGPT, chatHistory))
        {
            yield return assistantWord;
        }

        string MessageToString(ChatHistory.Message message)
        {
            return $"{message.AuthorRole}: {message.Content}\n------------------------\n";
        }
    }

    private static async IAsyncEnumerable<string> AssistantStreamMessageAsync(IChatCompletion chatGPT, ChatHistory chatHistory)
    {
        yield return "Assistant: ";
        string assistantMessage = string.Empty;
        await foreach (string message in chatGPT.GenerateMessageStreamAsync(chatHistory))
        {
            assistantMessage += message;
            yield return message;
        }

        yield return "\n------------------------\n";
        chatHistory.AddMessage(ChatHistory.AuthorRoles.Assistant, assistantMessage);
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

    #region Custom Chat Service

    private static async Task CustomChatSampleAsync()
    {
        Console.WriteLine("======== SK with Custom Chat ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        IChatCompletion Factory(IKernel k) => new MyChatCompletionService();
        // Add your chat completion service
        kernel.Config.AddChatCompletionService(Factory);

        IChatCompletion customChat = kernel.GetService<IChatCompletion>();
        ChatHistory chatHistory = await CustomPrepareChatHistoryAsync(customChat);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        foreach (var message in chatHistory.Messages)
        {
            Console.WriteLine($"{message.AuthorRole}: {message.Content}");
            Console.WriteLine("------------------------");
        }
    }

    private static async Task<ChatHistory> CustomPrepareChatHistoryAsync(IChatCompletion customChat)
    {
        var chatHistory = customChat.CreateNewChat("You are a my SK Custom Assistant");

        // First user message
        chatHistory.AddMessage(ChatHistory.AuthorRoles.User, "Hi, who are you?");

        // First bot message
        string reply = await customChat.GenerateMessageAsync(chatHistory);
        chatHistory.AddMessage(ChatHistory.AuthorRoles.Assistant, reply);

        return chatHistory;
    }

    private static async Task CustomChatStreamSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI ChatGPT - Stream ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        IChatCompletion Factory(IKernel k) => new MyChatCompletionService();
        // Add your chat completion service
        kernel.Config.AddChatCompletionService(Factory);

        IChatCompletion customChat = kernel.GetService<IChatCompletion>();

        var chat = customChat.CreateNewChat("You are a librarian, expert about books");

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");
        await foreach (var message in CustomStreamingChatAsync(customChat))
        {
            Console.Write(message);
        }
    }

    private static async IAsyncEnumerable<string> CustomStreamingChatAsync(IChatCompletion chatGPT)
    {
        var chatHistory = chatGPT.CreateNewChat("You are a my SK Custom Assistant");
        yield return MessageToString(chatHistory.Messages.Last());

        chatHistory.AddMessage(ChatHistory.AuthorRoles.User, "Hi, who are you?");
        yield return MessageToString(chatHistory.Messages.Last());

        await foreach (var assistantWord in AssistantStreamMessageAsync(chatGPT, chatHistory))
        {
            yield return assistantWord;
        }

        string MessageToString(ChatHistory.Message message)
        {
            return $"{message.AuthorRole}: {message.Content}\n------------------------\n";
        }
    }

    private sealed class MyChatCompletionService : IChatCompletion
    {
        private readonly string _outputAssistantResult = "Hi I'm your SK Custom Assistant and I'm here to help you to create custom chats like this. :)";

        public ChatHistory CreateNewChat(string instructions = "")
        {
            var chatHistory = new ChatHistory();

            if (!string.IsNullOrWhiteSpace(instructions))
            {
                chatHistory.AddMessage(ChatHistory.AuthorRoles.System, instructions);
            }

            return chatHistory;
        }

        public Task<string> GenerateMessageAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._outputAssistantResult);
        }

        public async IAsyncEnumerable<string> GenerateMessageStreamAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
        {
            var streamedOutput = this._outputAssistantResult.Split(' ');
            foreach (string word in streamedOutput)
            {
                await Task.Delay(200, cancellationToken);
                yield return $"{word} ";
            }
        }
    }

    #endregion
}
