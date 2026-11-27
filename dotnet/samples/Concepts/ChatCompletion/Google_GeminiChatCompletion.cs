// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate different ways of using chat completion with Google VertexAI and GoogleAI APIs.
/// </summary>
public sealed class Google_GeminiChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GoogleAIUsingChatCompletion()
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

        await this.ProcessChatAsync(kernel);
    }

    [Fact]
    public async Task VertexAIUsingChatCompletion()
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

        await this.ProcessChatAsync(kernel);
    }

    private async Task ProcessChatAsync(Kernel kernel)
    {
        List<ChatMessage> chatHistory = [new(ChatRole.System, "You are an expert in the tool shop.")];
        var chatClient = kernel.GetRequiredService<IChatClient>();

        // First user message
        chatHistory.Add(new(ChatRole.User, "Hi, I'm looking for new power tools, any suggestion?"));
        await MessageOutputAsync(chatHistory);

        // First assistant message
        var reply = await chatClient.GetResponseAsync(chatHistory);
        chatHistory.AddMessages(reply);
        await MessageOutputAsync(chatHistory);

        // Second user message
        chatHistory.Add(new(ChatRole.User, "I'm looking for a drill, a screwdriver and a hammer."));
        await MessageOutputAsync(chatHistory);

        // Second assistant message
        reply = await chatClient.GetResponseAsync(chatHistory);
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
