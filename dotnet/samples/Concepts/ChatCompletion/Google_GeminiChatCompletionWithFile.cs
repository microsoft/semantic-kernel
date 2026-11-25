// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Resources;
using TextContent = Microsoft.Extensions.AI.TextContent;

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

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(TestConfiguration.GoogleAI.Gemini.ModelId));
        Kernel kernel = builder.Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "You are a friendly assistant."),
            new(ChatRole.User,
            [
                new TextContent("What's in this file?"),
                new DataContent(fileBytes, "application/pdf")
            ])
        ];

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }

    [Fact]
    public async Task VertexAIChatCompletionWithLocalFile()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion With Local File =============");

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

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "You are a friendly assistant."),
            new(ChatRole.User,
            [
                new TextContent("What's in this file?"),
                new DataContent(fileBytes, "application/pdf"),
            ])
        ];

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }

    [Fact]
    public async Task GoogleAIChatCompletionWithBase64DataUri()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion With Base64 Data Uri =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(TestConfiguration.GoogleAI.Gemini.ModelId));
        Kernel kernel = builder.Build();

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "You are a friendly assistant."),
            new(ChatRole.User,
            [
                new TextContent("What's in this file?"),
                new DataContent(dataUri)
                // Google AI Gemini API does not support arbitrary URIs, so inline Base64 data URIs are sent as inline data.
            ])
        ];

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }

    [Fact]
    public async Task VertexAIChatCompletionWithBase64DataUri()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion With Base64 Data Uri =============");

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

        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        List<ChatMessage> chatHistory =
        [
            new(ChatRole.System, "You are a friendly assistant."),
            new(ChatRole.User,
            [
                new TextContent("What's in this file?"),
                new DataContent(dataUri)
                // Vertex AI also supports GCS URIs within the same project via UriContent:
                // new UriContent("gs://generativeai-downloads/files/employees.pdf", "application/pdf")
            ])
        ];

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var reply = await chatClient.GetResponseAsync(chatHistory);

        Console.WriteLine(reply.Text);
    }
}
