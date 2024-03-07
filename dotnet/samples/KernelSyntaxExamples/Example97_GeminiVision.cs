// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public sealed class Example97_GeminiVision : BaseTest
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

        var chatHistory = new ChatHistory();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Load the image from the resources
        await using var stream = EmbeddedResource.ReadStream("sample_image.jpg")!;
        using var binaryReader = new BinaryReader(stream);
        var bytes = binaryReader.ReadBytes((int)stream.Length);

        chatHistory.AddUserMessage(new ChatMessageContentItemCollection
        {
            new TextContent("What’s in this image?"),
            // Google AI Gemini API requires the image to be in base64 format, doesn't support URI
            // You have to always provide the mimeType for the image
            new ImageContent(bytes) { MimeType = "image/jpeg" },
        });

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        WriteLine(reply.Content);
    }

    private async Task VertexAIGeminiAsync()
    {
        this.WriteLine("===== Vertex AI Gemini API =====");

        string geminiBearerKey = TestConfiguration.VertexAI.BearerKey;
        string geminiModelId = "gemini-pro-vision";
        string geminiLocation = TestConfiguration.VertexAI.Location;
        string geminiProject = TestConfiguration.VertexAI.ProjectId;

        if (geminiBearerKey is null || geminiLocation is null || geminiProject is null)
        {
            this.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiChatCompletion(
                modelId: geminiModelId,
                bearerKey: geminiBearerKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        var chatHistory = new ChatHistory();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Load the image from the resources
        await using var stream = EmbeddedResource.ReadStream("sample_image.jpg")!;
        using var binaryReader = new BinaryReader(stream);
        var bytes = binaryReader.ReadBytes((int)stream.Length);

        chatHistory.AddUserMessage(new ChatMessageContentItemCollection
        {
            new TextContent("What’s in this image?"),
            // Vertex AI Gemini API supports both base64 and URI format
            // You have to always provide the mimeType for the image
            new ImageContent(bytes) { MimeType = "image/jpeg" },
            // The Cloud Storage URI of the image to include in the prompt.
            // The bucket that stores the file must be in the same Google Cloud project that's sending the request.
            // new ImageContent(new Uri("gs://generativeai-downloads/images/scones.jpg"),
            //    metadata: new Dictionary<string, object?> { { "mimeType", "image/jpeg" } })
        });

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        WriteLine(reply.Content);
    }

    public Example97_GeminiVision(ITestOutputHelper output) : base(output) { }
}
