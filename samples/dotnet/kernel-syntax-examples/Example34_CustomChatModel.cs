// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to plug use a custom chat model.
 *
 * This might be useful in a few scenarios, for example:
 * - You are not using OpenAI or Azure OpenAI models
 * - You are using OpenAI/Azure OpenAI models but the models are behind a web service with a different API schema
 * - You want to use a local model
 */
public sealed class MyChatCompletionService : IChatCompletion
{
    private const string OutputAssistantResult = "Hi I'm your SK Custom Assistant and I'm here to help you to create custom chats like this. :)";

    public ChatHistory CreateNewChat(string instructions = "")
    {
        var chatHistory = new ChatHistory();

        if (!string.IsNullOrWhiteSpace(instructions))
        {
            chatHistory.AddMessage(ChatHistory.AuthorRoles.System, instructions);
        }

        return chatHistory;
    }

    public async Task<string> GenerateMessageAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        // Forcing a 2 sec delay (Simulating custom LLM lag)
        await Task.Delay(2000, cancellationToken);

        return OutputAssistantResult;
    }

    public async IAsyncEnumerable<string> GenerateMessageStreamAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var streamedOutput = OutputAssistantResult.Split(' ');
        foreach (string word in streamedOutput)
        {
            await Task.Delay(200, cancellationToken);
            yield return $"{word} ";
        }
    }
}

// ReSharper disable once InconsistentNaming
public static class Example34_CustomChatModel
{
    public static async Task RunAsync()
    {
        await CustomChatStreamSampleAsync();
        await CustomChatSampleAsync();

        /* Output:

        Chat content:
        ------------------------
        System: You are a my SK Custom Assistant
        ------------------------
        User: Hi, who are you?
        ------------------------
        Assistant: Hi I'm your SK Custom Assistant and I'm here to help you to create custom chats like this. :)
        ------------------------
        */
    }

    private static async Task CustomChatSampleAsync()
    {
        Console.WriteLine("======== Custom LLM - Chat Completion ========");

        IChatCompletion Factory(ILogger l) => new MyChatCompletionService();

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithDefaultAIService<IChatCompletion>(Factory)
            .Build();

        IChatCompletion customChat = kernel.GetService<IChatCompletion>();

        await StartChatAsync(customChat);
    }

    private static async Task StartChatAsync(IChatCompletion customChat)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = customChat.CreateNewChat("You are a my SK Custom Assistant");

        // First user message
        chatHistory.AddMessage(ChatHistory.AuthorRoles.User, "Hi, who are you?");
        await MessageOutputAsync(chatHistory);

        // First bot assistant message
        string reply = await customChat.GenerateMessageAsync(chatHistory);
        chatHistory.AddMessage(ChatHistory.AuthorRoles.Assistant, reply);
        await MessageOutputAsync(chatHistory);
    }

    private static async Task CustomChatStreamSampleAsync()
    {
        Console.WriteLine("======== Custom LLM - Chat Completion Streaming ========");

        IChatCompletion Factory(ILogger l) => new MyChatCompletionService();

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithDefaultAIService<IChatCompletion>(Factory)
            .Build();

        IChatCompletion customChat = kernel.GetService<IChatCompletion>();

        await StartStreamingChatAsync(customChat);
    }

    private static async Task StartStreamingChatAsync(IChatCompletion customChat)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = customChat.CreateNewChat("You are a my SK Custom Assistant");
        await MessageOutputAsync(chatHistory);

        // First user message
        chatHistory.AddMessage(ChatHistory.AuthorRoles.User, "Hi, who are you?");
        await MessageOutputAsync(chatHistory);

        // Bot assistant message
        await StreamMessageOutputAsync(customChat, chatHistory);
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Messages.Last();

        Console.WriteLine($"{message.AuthorRole}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }

    private static async Task StreamMessageOutputAsync(IChatCompletion customChat, ChatHistory chatHistory,
        ChatHistory.AuthorRoles authorRole = ChatHistory.AuthorRoles.Assistant)
    {
        Console.Write($"{authorRole}: ");
        string fullMessage = string.Empty;

        await foreach (string message in customChat.GenerateMessageStreamAsync(chatHistory))
        {
            fullMessage += message;
            Console.Write(message);
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }
}
