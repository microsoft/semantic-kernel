// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

public sealed class Anthropic_Vision(ITestOutputHelper output) : BaseTest(output)
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

        var chatHistory = new ChatHistory("Your job is describing images.");
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Load the image from the resources
        await using var stream = EmbeddedResource.ReadStream("sample_image.jpg")!;
        using var binaryReader = new BinaryReader(stream);
        var bytes = binaryReader.ReadBytes((int)stream.Length);

        chatHistory.AddUserMessage(
        [
            new TextContent("What’s in this image?"),
            // Vertex AI Gemini API supports both base64 and URI format
            // You have to always provide the mimeType for the image
            new ImageContent(bytes, "image/jpeg"),
            // The Cloud Storage URI of the image to include in the prompt.
            // The bucket that stores the file must be in the same Google Cloud project that's sending the request.
            // new ImageContent(new Uri("gs://generativeai-downloads/images/scones.jpg"),
            //    metadata: new Dictionary<string, object?> { { "mimeType", "image/jpeg" } })
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }
}
