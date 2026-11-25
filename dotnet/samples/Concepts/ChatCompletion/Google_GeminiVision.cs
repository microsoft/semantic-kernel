// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Resources;
using TextContent = Microsoft.Extensions.AI.TextContent;

namespace ChatCompletion;

/// <summary>
/// This sample shows how to use Google's Gemini Chat Completion model with vision using VertexAI and GoogleAI APIs.
/// </summary>
public sealed class Google_GeminiVision(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GoogleAIChatCompletionWithVision()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion with vision =============");

        string geminiApiKey = TestConfiguration.GoogleAI.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null)
        {
            Console.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        using var googleClient = new Google.GenAI.Client(apiKey: geminiApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(geminiModelId));
        Kernel kernel = builder.Build();

        var chatClient = kernel.GetRequiredService<IChatClient>();

        // Load the image from the resources
        await using var stream = EmbeddedResource.ReadStream("sample_image.jpg")!;
        using var binaryReader = new BinaryReader(stream);
        var bytes = binaryReader.ReadBytes((int)stream.Length);

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "Your job is describing images."),
            new(ChatRole.User,
            [
                new TextContent("What’s in this image?"),
                // Google AI Gemini API requires the image to be inline data with a media type
                new DataContent(bytes, "image/jpeg"),
            ])
        ];

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }

    [Fact]
    public async Task VertexAIChatCompletionWithVision()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion with vision =============");

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

        var chatClient = kernel.GetRequiredService<IChatClient>();

        // Load the image from the resources
        await using var stream = EmbeddedResource.ReadStream("sample_image.jpg")!;
        using var binaryReader = new BinaryReader(stream);
        var bytes = binaryReader.ReadBytes((int)stream.Length);

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "Your job is describing images."),
            new(ChatRole.User,
            [
                new TextContent("What’s in this image?"),
                // Vertex AI Gemini API supports both inline data and GCS URIs
                new DataContent(bytes, "image/jpeg"),
                // The Cloud Storage URI of the image to include in the prompt.
                // The bucket that stores the file must be in the same Google Cloud project that's sending the request.
                // new UriContent("gs://generativeai-downloads/images/scones.jpg", "image/jpeg")
            ])
        ];

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }
}
