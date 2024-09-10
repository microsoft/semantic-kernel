// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

public sealed class Anthropic_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task SampleAsync()
    {
        Console.WriteLine("============= Anthropic - Claude Chat  Streaming =============");

        string apiKey = TestConfiguration.AnthropicAI.ApiKey;
        string modelId = TestConfiguration.AnthropicAI.ModelId;

        Assert.NotNull(apiKey);
        Assert.NotNull(modelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddAnthropicChatCompletion(
                modelId: modelId,
                apiKey: apiKey)
            .Build();

        await this.StreamingChatAsync(kernel);
    }

    private async Task StreamingChatAsync(Kernel kernel)
    {
        Console.WriteLine("======== Streaming Chat ========");

        var chatHistory = new ChatHistory("You are an expert in the tool shop.");
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

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

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
