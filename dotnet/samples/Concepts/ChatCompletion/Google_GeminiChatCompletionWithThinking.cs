// Copyright (c) Microsoft. All rights reserved.

using Google.GenAI.Types;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate different ways of using chat completion with Google AI API.
/// <para>
/// Gemini 3 and later models use thinking levels instead of token budgets.
/// See: https://aistudio.google.com/docs/thinking
/// </para>
/// </summary>
public sealed class Google_GeminiChatCompletionWithThinking(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GoogleAIChatCompletionUsingLowThinkingLevel()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion using Low Thinking Level =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(geminiModelId));
        Kernel kernel = builder.Build();

        List<ChatMessage> chatHistory = [new(ChatRole.System, "You are an expert in the tool shop.")];
        var chatClient = kernel.GetRequiredService<IChatClient>();
        // The native SDK configuration preserves provider-specific thinking options.
        var chatOptions = new ChatOptions
        {
            RawRepresentationFactory = _ => new GenerateContentConfig
            {
                ThinkingConfig = new() { ThinkingLevel = ThinkingLevel.Low }
            }
        };

        // First user message
        chatHistory.Add(new(ChatRole.User, "Hi, I'm looking for new power tools, any suggestion?"));
        await MessageOutputAsync(chatHistory);

        // First assistant message
        var reply = await chatClient.GetResponseAsync(chatHistory, chatOptions);
        chatHistory.AddMessages(reply);
        await MessageOutputAsync(chatHistory);
    }

    [Fact]
    public async Task GoogleAIChatCompletionUsingThinkingLevel()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion using High Thinking Level =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(geminiModelId));
        Kernel kernel = builder.Build();

        List<ChatMessage> chatHistory = [new(ChatRole.System, "You are an expert in the tool shop.")];
        var chatClient = kernel.GetRequiredService<IChatClient>();
        // Configure a Gemini 3 or later model to use thinking levels instead of a token budget.
        var chatOptions = new ChatOptions
        {
            RawRepresentationFactory = _ => new GenerateContentConfig
            {
                ThinkingConfig = new() { ThinkingLevel = ThinkingLevel.High }
            }
        };

        // First user message
        chatHistory.Add(new(ChatRole.User, "Hi, I'm looking for new power tools, any suggestion?"));
        await MessageOutputAsync(chatHistory);

        // First assistant message
        var reply = await chatClient.GetResponseAsync(chatHistory, chatOptions);
        chatHistory.AddMessages(reply);
        await MessageOutputAsync(chatHistory);
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
}
