// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;

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
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        var chatHistory = new MyChatHistory();

        if (!string.IsNullOrWhiteSpace(instructions))
        {
            chatHistory.Add(new MyChatMessage(MyRoles.SuperUser, instructions));
        }

        return chatHistory;
    }

    public Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<IReadOnlyList<IChatResult>>(new List<IChatResult>
        {
            new MyChatStreamingResult(MyRoles.Bot, "Hi I'm your SK Custom Assistant and I'm here to help you to create custom chats like this. :)")
        });
    }

    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        return (new List<IChatStreamingResult>
        {
            new MyChatStreamingResult(MyRoles.Bot, "Hi I'm your SK Custom Assistant and I'm here to help you to create custom chats like this. :)")
        }).ToAsyncEnumerable();
    }
}

public class MyChatStreamingResult : IChatStreamingResult
{
    private readonly ChatMessageBase _message;
    private readonly MyRoles _role;
    public ModelResult ModelResult { get; private set; }

    public MyChatStreamingResult(MyRoles role, string content)
    {
        this._role = role;
        this._message = new MyChatMessage(role, content);
        this.ModelResult = new ModelResult(content);
    }

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._message);
    }

    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var streamedOutput = this._message.Content.Split(' ');
        foreach (string word in streamedOutput)
        {
            await Task.Delay(100, cancellationToken);
            yield return new MyChatMessage(this._role, $"{word} ");
        }
    }
}

public class MyChatMessage : ChatMessageBase
{
    public MyChatMessage(MyRoles role, string content) : base(new AuthorRole(role.ToString()), content)
    {
    }
}

public class MyChatHistory : ChatHistory
{
    public void AddMessage(MyRoles role, string message)
    {
        this.Add(new MyChatMessage(role, message));
    }
}

public enum MyRoles
{
    SuperUser,
    User,
    Bot
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

        IChatCompletion customChat = new MyChatCompletionService();

        await StartChatAsync(customChat);
    }

    private static async Task StartChatAsync(IChatCompletion customChat)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = (MyChatHistory)customChat.CreateNewChat("You are a my SK Custom Assistant");

        // First user message
        chatHistory.AddMessage(MyRoles.User, "Hi, who are you?");
        await MessageOutputAsync(chatHistory);

        // First bot assistant message
        string reply = await customChat.GenerateMessageAsync(chatHistory);
        chatHistory.AddMessage(MyRoles.Bot, reply);
        await MessageOutputAsync(chatHistory);
    }

    private static async Task CustomChatStreamSampleAsync()
    {
        Console.WriteLine("======== Custom LLM - Chat Completion Streaming ========");

        IChatCompletion customChat = new MyChatCompletionService();

        await StartStreamingChatAsync(customChat);
    }

    private static async Task StartStreamingChatAsync(IChatCompletion customChat)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = (MyChatHistory)customChat.CreateNewChat("You are a my SK Custom Assistant");
        await MessageOutputAsync(chatHistory);

        // First user message
        chatHistory.AddMessage(MyRoles.User, "Hi, who are you?");
        await MessageOutputAsync(chatHistory);

        // Bot assistant message
        await StreamMessageOutputAsync(customChat, chatHistory);
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(MyChatHistory chatHistory)
    {
        var message = chatHistory.Messages.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }

    private static async Task StreamMessageOutputAsync(IChatCompletion customChat, MyChatHistory chatHistory, MyRoles myModelRole = MyRoles.Bot)
    {
        Console.Write($"{myModelRole}: ");
        string fullMessage = string.Empty;

        await foreach (string message in customChat.GenerateMessageStreamAsync(chatHistory))
        {
            fullMessage += message;
            Console.Write(message);
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(myModelRole, fullMessage);
    }
}
