// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public sealed class Example81_GeminiChatCompletion : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== Gemini Chat Completion ========");

        await GoogleAIGeminiAsync();
        await VertexAIGeminiAsync();
    }

    private async Task GoogleAIGeminiAsync()
    {
        this.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            this.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiChatCompletion(
                modelId: geminiModelId,
                apiKey: geminiApiKey)
            .Build();

        await RunSampleAsync(kernel);
    }

    private async Task VertexAIGeminiAsync()
    {
        this.WriteLine("===== Vertex AI Gemini API =====");

        string geminiApiKey = TestConfiguration.VertexAI.ApiKey;
        string geminiModelId = TestConfiguration.VertexAI.Gemini.ModelId;
        string geminiLocation = TestConfiguration.VertexAI.Location;
        string geminiProject = TestConfiguration.VertexAI.ProjectId;

        if (geminiApiKey is null || geminiModelId is null || geminiLocation is null || geminiProject is null)
        {
            this.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
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

    private async Task RunSampleAsync(Kernel kernel)
    {
        await SimpleChatAsync(kernel);
        await StreamingChatAsync(kernel);
    }

    private async Task StreamingChatAsync(Kernel kernel)
    {
        this.WriteLine("======== Streaming Chat ========");

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

    private async Task SimpleChatAsync(Kernel kernel)
    {
        this.WriteLine("======== Simple Chat ========");

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
    private Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        this.WriteLine($"{message.Role}: {message.Content}");
        this.WriteLine("------------------------");

        return Task.CompletedTask;
    }

    private async Task<ChatMessageContent> MessageOutputAsync(IAsyncEnumerable<StreamingChatMessageContent> streamingChat)
    {
        bool first = true;
        StringBuilder messageBuilder = new();
        await foreach (var chatMessage in streamingChat)
        {
            if (first)
            {
                this.Write($"{chatMessage.Role}: ");
                first = false;
            }

            this.Write(chatMessage.Content);
            messageBuilder.Append(chatMessage.Content);
        }

        this.WriteLine();
        this.WriteLine("------------------------");
        return new ChatMessageContent(AuthorRole.Assistant, messageBuilder.ToString());
    }

    public Example81_GeminiChatCompletion(ITestOutputHelper output) : base(output) { }
}
