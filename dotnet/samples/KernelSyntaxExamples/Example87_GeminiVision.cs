// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public sealed class Example87_GeminiVision : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== Gemini chat with vision ========");

        await GoogleAIGeminiAsync();
        await VertexAIGeminiAsync();
    }

    private async Task GoogleAIGeminiAsync()
    {
        this.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.ApiKey;
        string geminiModelId = "gemini-pro-vision";

        if (geminiApiKey is null)
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
        string geminiModelId = "gemini-pro-vision";
        string geminiLocation = TestConfiguration.VertexAI.Location;
        string geminiProject = TestConfiguration.VertexAI.ProjectId;

        if (geminiApiKey is null || geminiLocation is null || geminiProject is null)
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
        var chatHistory = new ChatHistory();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        chatHistory.AddUserMessage(new ChatMessageContentItemCollection
        {
            new TextContent("What’s in this image?"),
            new ImageContent(new BinaryData(EmbeddedResource.ReadStream("sample_image.jpg")))
        });

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        WriteLine(reply.Content);
    }

    public Example87_GeminiVision(ITestOutputHelper output) : base(output) { }
}
