// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

// This example shows how to use OpenAI chat completion with PDF files.
public class OpenAI_ChatCompletionWithFile(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task LocalFileAsync()
    {
        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage(
        [
            new TextContent("What’s in this file?"),
            new BinaryContent(fileBytes, "application/pdf")
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    [Fact]
    public async Task DateUriFileAsync()
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
            new TextContent("What’s in this file?"),
            new BinaryContent(dataUri)
        ]);

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }
}
