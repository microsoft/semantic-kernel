// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

/**
 * This example shows how to use GPT Vision model with different content types (text and image).
 */
// ReSharper disable once InconsistentNaming
public static class Example68_GPTVision
{
    public static async Task RunAsync()
    {
        const string ImageUri = "https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg";

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4-vision-preview", TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(new ChatMessageContentItemCollection
        {
            new TextContent("What’s in this image?"),
            new ImageContent(new Uri(ImageUri))
        });

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);

        Console.ReadKey();
    }
}
