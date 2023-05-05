// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT API
 */
// ReSharper disable once InconsistentNaming
public static class Example33_CustomChat
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

    private static async Task CustomChatSampleAsync()
    {
        Console.WriteLine("======== Custom Chat ========");

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
        Console.WriteLine("======== Custom Chat - Stream ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        IChatCompletion Factory(IKernel k) => new MyChatCompletionService();
        // Add your chat completion service
        kernel.Config.AddChatCompletionService(Factory);

        IChatCompletion customChat = kernel.GetService<IChatCompletion>();

        var chat = customChat.CreateNewChat("You are a my SK Custom Assistant");

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

        public async IAsyncEnumerable<string> GenerateMessageStreamAsync(
            ChatHistory chat,
            ChatRequestSettings? requestSettings = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var streamedOutput = this._outputAssistantResult.Split(' ');
            foreach (string word in streamedOutput)
            {
                await Task.Delay(200, cancellationToken);
                yield return $"{word} ";
            }
        }
    }
}
