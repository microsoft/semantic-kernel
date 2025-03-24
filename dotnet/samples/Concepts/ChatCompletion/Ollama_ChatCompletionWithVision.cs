// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

/// <summary>
/// This sample shows how to use llama3.2-vision model with different content types (text and image).
/// </summary>
public class Ollama_ChatCompletionWithVision(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample uses a local image file and sends it to the model along
    /// with a text message the get the description of the image.
    /// </summary>
    [Fact]
    public async Task GetLocalImageDescription()
    {
        Console.WriteLine($"======== Ollama - {nameof(GetLocalImageDescription)} ========");

        var imageBytes = await EmbeddedResource.ReadAllAsync("sample_image.jpg");

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatCompletion(modelId: "llama3.2-vision", endpoint: new Uri(TestConfiguration.Ollama.Endpoint))
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(
        [
            new TextContent("What’s in this image?"),
            new ImageContent(imageBytes, "image/jpg")
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }
}
