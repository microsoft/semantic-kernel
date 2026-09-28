// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace ChatCompletion;

/// <summary>
/// This sample shows how to use binary file and inline Base64 inputs, like PDFs, with Google Gemini's chat completion.
/// </summary>
public class Google_GeminiChatCompletionWithFile(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GoogleAIChatCompletionWithLocalFile()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion With Local File =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiChatCompletion(TestConfiguration.GoogleAI.Gemini.ModelId, TestConfiguration.GoogleAI.ApiKey)
            .Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        var chatHistory = new ChatHistory("You are a friendly assistant.");
        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(fileBytes, "application/pdf")
        ]);

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    [Fact]
    public async Task VertexAIChatCompletionWithLocalFile()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion With Local File =============");

        Assert.NotNull(TestConfiguration.VertexAI.BearerKey);
        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
        Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiChatCompletion(
                modelId: TestConfiguration.VertexAI.Gemini.ModelId,
                bearerKey: TestConfiguration.VertexAI.BearerKey,
                location: TestConfiguration.VertexAI.Location,
                projectId: TestConfiguration.VertexAI.ProjectId)
            .Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        var chatHistory = new ChatHistory("You are a friendly assistant.");
        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(fileBytes, "application/pdf"),
        ]);

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    [Fact]
    public async Task GoogleAIChatCompletionWithBase64DataUri()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion With Base64 Data Uri =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiChatCompletion(TestConfiguration.GoogleAI.Gemini.ModelId, TestConfiguration.GoogleAI.ApiKey)
            .Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        var chatHistory = new ChatHistory("You are a friendly assistant.");
        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(dataUri)
            // Google AI Gemini AI does not support arbitrary URIs but we can convert a Base64 URI into InlineData with the correct mimeType.
        ]);

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }

    [Fact]
    public async Task VertexAIChatCompletionWithBase64DataUri()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion With Base64 Data Uri =============");

        Assert.NotNull(TestConfiguration.VertexAI.BearerKey);
        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
        Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiChatCompletion(
                modelId: TestConfiguration.VertexAI.Gemini.ModelId,
                bearerKey: TestConfiguration.VertexAI.BearerKey,
                location: TestConfiguration.VertexAI.Location,
                projectId: TestConfiguration.VertexAI.ProjectId)
            .Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        var chatHistory = new ChatHistory("You are a friendly assistant.");
        chatHistory.AddUserMessage(
        [
            new TextContent("What's in this file?"),
            new BinaryContent(dataUri)
            // Vertex AI API does not support URIs outside of inline Base64 or GCS buckets within the same project. The bucket that stores the file must be in the same Google Cloud project that's sending the request. You must always provide the mimeType via the metadata property.
            // var content = new BinaryContent(gs://generativeai-downloads/files/employees.pdf);
            // content.Metadata = new Dictionary<string, object?> { { "mimeType", "application/pdf" } };
        ]);

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory);

        Console.WriteLine(reply.Content);
    }
}
