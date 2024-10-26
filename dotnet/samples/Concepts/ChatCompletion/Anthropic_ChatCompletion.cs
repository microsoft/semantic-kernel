// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

public sealed class Anthropic_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task SampleAsync()
    {
        Console.WriteLine("============= Anthropic - Claude Chat Completion =============");

        string apiKey = TestConfiguration.AnthropicAI.ApiKey;
        string modelId = TestConfiguration.AnthropicAI.ModelId;

        Assert.NotNull(apiKey);
        Assert.NotNull(modelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddAnthropicChatCompletion(
                modelId: modelId,
                apiKey: apiKey)
            .Build();

        await SimpleChatAsync(kernel);
    }

    private async Task SimpleChatAsync(Kernel kernel)
    {
        Console.WriteLine("======== Simple Chat ========");

        var chatHistory = new ChatHistory("You are an expert in the tool shop.");
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

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }
}
