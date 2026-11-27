// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate different ways of using chat completion with Google VertexAI and GoogleAI APIs.
/// </summary>
public sealed class Google_GeminiChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GoogleAIUsingStreamingChatCompletion()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion =============");

        string geminiApiKey = TestConfiguration.GoogleAI.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            Console.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        using var googleClient = new Google.GenAI.Client(apiKey: geminiApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(geminiModelId));
        Kernel kernel = builder.Build();

        await this.ProcessStreamingChatAsync(kernel);
    }

    [Fact]
    public async Task VertexAIUsingStreamingChatCompletion()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion =============");

        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
        Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

        // The Google SDK discovers application default credentials and refreshes tokens automatically.
        using var googleClient = new Google.GenAI.Client(
            vertexAI: true,
            project: TestConfiguration.VertexAI.ProjectId,
            location: TestConfiguration.VertexAI.Location);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(TestConfiguration.VertexAI.Gemini.ModelId));
        Kernel kernel = builder.Build();

        await this.ProcessStreamingChatAsync(kernel);
    }

    private async Task ProcessStreamingChatAsync(Kernel kernel)
    {
        List<ChatMessage> chatHistory = [new(ChatRole.System, "You are an expert in the tool shop.")];
        var chatClient = kernel.GetRequiredService<IChatClient>();

        // First user message
        chatHistory.Add(new(ChatRole.User, "Hi, I'm looking for alternative coffee brew methods, can you help me?"));
        await MessageOutputAsync(chatHistory);

        // First assistant message
        var streamingChat = chatClient.GetStreamingResponseAsync(chatHistory);
        var reply = await MessageOutputAsync(streamingChat);
        chatHistory.Add(reply);

        // Second user message
        chatHistory.Add(new(ChatRole.User, "Give me the best speciality coffee roasters."));
        await MessageOutputAsync(chatHistory);

        // Second assistant message
        streamingChat = chatClient.GetStreamingResponseAsync(chatHistory);
        reply = await MessageOutputAsync(streamingChat);
        chatHistory.Add(reply);
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private Task MessageOutputAsync(IList<ChatMessage> chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Text}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }

    private async Task<ChatMessage> MessageOutputAsync(IAsyncEnumerable<ChatResponseUpdate> streamingChat)
    {
        bool first = true;
        StringBuilder messageBuilder = new();
        await foreach (var chatMessage in streamingChat)
        {
            if (first)
            {
                Console.Write($"{chatMessage.Role ?? ChatRole.Assistant}: ");
                first = false;
            }

            Console.Write(chatMessage.Text);
            messageBuilder.Append(chatMessage.Text);
        }

        Console.WriteLine();
        Console.WriteLine("------------------------");
        return new ChatMessage(ChatRole.Assistant, messageBuilder.ToString());
    }
}
