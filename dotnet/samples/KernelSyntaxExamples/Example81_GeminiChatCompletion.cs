#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

public static class Example81_GeminiChatCompletion
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Gemini Chat Completion ========");

        await GoogleAIGeminiAsync();
        await VertexAIGeminiAsync();
    }

    private static async Task GoogleAIGeminiAsync()
    {
        Console.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            Console.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiChatCompletion(
                modelId: geminiModelId,
                apiKey: geminiApiKey)
            .Build();

        await RunSampleAsync(kernel);
    }

    private static async Task VertexAIGeminiAsync()
    {
        Console.WriteLine("===== Vertex AI Gemini API =====");

        string geminiApiKey = TestConfiguration.VertexAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.VertexAI.Gemini.ModelId;
        string geminiLocation = TestConfiguration.VertexAI.Gemini.Location;
        string geminiProject = TestConfiguration.VertexAI.Gemini.ProjectId;

        if (geminiApiKey is null || geminiModelId is null || geminiLocation is null || geminiProject is null)
        {
            Console.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiChatCompletion(
                modelId: geminiModelId,
                apiKey: geminiApiKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        await RunSampleAsync(kernel);
    }

    private static async Task RunSampleAsync(Kernel kernel)
    {
        await SimpleChatAsync(kernel);
        await StreamingChatAsync(kernel);
    }

    private static async Task StreamingChatAsync(Kernel kernel)
    {
        Console.WriteLine("======== Streaming Chat ========");

        var chatHistory = new ChatHistory();
        var chat = kernel.GetRequiredService<IChatCompletionService>();

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for alternative coffee brew methods, can you help me?");
        await MessageOutputAsync(chatHistory);

        // First bot assistant message
        var streamingChat = chat.GetStreamingChatMessageContentsAsync(chatHistory);
        var reply = await MessageOutputAsync(streamingChat);
        chatHistory.Add(reply);

        // Second user message
        chatHistory.AddUserMessage("Give me the best speciality coffee roasters.");
        await MessageOutputAsync(chatHistory);

        // Second bot assistant message
        streamingChat = chat.GetStreamingChatMessageContentsAsync(chatHistory);
        reply = await MessageOutputAsync(streamingChat);
        chatHistory.Add(reply);
    }

    private static async Task SimpleChatAsync(Kernel kernel)
    {
        Console.WriteLine("======== Simple Chat ========");

        var chatHistory = new ChatHistory();
        var chat = kernel.GetRequiredService<IChatCompletionService>();

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for new power tools, any suggestion?");
        await MessageOutputAsync(chatHistory);

        // First bot assistant message
        var reply = await chat.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        await MessageOutputAsync(chatHistory);

        // Second user message
        chatHistory.AddUserMessage("I'm looking for a drill, a screwdriver and a hammer.");
        await MessageOutputAsync(chatHistory);

        // Second bot assistant message
        reply = await chat.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        await MessageOutputAsync(chatHistory);
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

    private static async Task<ChatMessageContent> MessageOutputAsync(IAsyncEnumerable<StreamingChatMessageContent> streamingChat)
    {
        bool first = true;
        StringBuilder messageBuilder = new();
        await foreach (var chatMessage in streamingChat)
        {
            if (first)
            {
                Console.Write($"{chatMessage.Role}: ");
                first = false;
            }

            Console.Write(chatMessage.Content);
            messageBuilder.Append(chatMessage.Content);
        }

        Console.WriteLine();
        Console.WriteLine("------------------------");
        return new ChatMessageContent(AuthorRole.Assistant, messageBuilder.ToString());
    }
}
