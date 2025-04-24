// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

/// <summary>
/// This example shows how to use binary files input with OpenAI's chat completion.
/// </summary>
public class OpenAI_ChatCompletionWithFile(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This uses a local file as input for your chat
    /// </summary>
    [Fact]
    public async Task UsingLocalFileInChatCompletion()
    {
        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(fileBytes, "application/pdf")
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    /// <summary>
    /// This uses a Base64 data URI as a binary file input for your chat
    /// </summary>
    [Fact]
    public async Task UsingBase64DataUriInChatCompletion()
    {
        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(dataUri)
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }
}
