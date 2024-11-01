// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

// This example shows how to use GPT Vision model with different content types (text and image).
public class OpenAI_ChatCompletionWithVision(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RemoteImageAsync()
    {
        const string ImageUri = "https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg";

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4-vision-preview", TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(
        [
            new TextContent("What’s in this image?"),
            new ImageContent(new Uri(ImageUri))
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    [Fact]
    public async Task LocalImageAsync()
    {
        var imageBytes = await EmbeddedResource.ReadAllAsync("sample_image.jpg");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4-vision-preview", TestConfiguration.OpenAI.ApiKey)
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
