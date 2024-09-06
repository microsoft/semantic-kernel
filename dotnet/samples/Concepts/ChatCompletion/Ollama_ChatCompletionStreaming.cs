// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate the ways different content types are streamed by Ollama via the chat completion service.
/// </summary>
public class Ollama_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates chat completion streaming using Ollama.
    /// </summary>
    [Fact]
    public Task StreamChatAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("======== Ollama - Chat Completion Streaming ========");

        var chatService = new OllamaChatCompletionService(
            endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
            modelId: TestConfiguration.Ollama.ModelId);

        return this.StartStreamingChatAsync(chatService);
    }

    [Fact]
    public async Task StreamChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatCompletion(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());

        Console.WriteLine(reply);
    }

    /// <summary>
    /// This example demonstrates how the chat completion service streams text content.
    /// It shows how to access the response update via StreamingChatMessageContent.Content property
    /// and alternatively via the StreamingChatMessageContent.Items property.
    /// </summary>
    [Fact]
    public async Task StreamTextFromChatAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("======== Stream Text from Chat Content ========");

        // Create chat completion service
        var chatService = new OllamaChatCompletionService(
            endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
            modelId: TestConfiguration.Ollama.ModelId);

        // Create chat history with initial system and user messages
        ChatHistory chatHistory = new("You are a librarian, an expert on books.");
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions.");
        chatHistory.AddUserMessage("I love history and philosophy. I'd like to learn something new about Greece, any suggestion?");

        // Start streaming chat based on the chat history
        await foreach (StreamingChatMessageContent chatUpdate in chatService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            // Access the response update via StreamingChatMessageContent.Content property
            Console.Write(chatUpdate.Content);

            // Alternatively, the response update can be accessed via the StreamingChatMessageContent.Items property
            Console.Write(chatUpdate.Items.OfType<StreamingTextContent>().FirstOrDefault());
        }
    }

    private async Task StartStreamingChatAsync(IChatCompletionService chatCompletionService)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        this.OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        // First assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        this.OutputLastMessage(chatHistory);

        // Second assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);
    }

    private async Task StreamMessageOutputAsync(IChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}");
                roleWritten = true;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                fullMessage += chatUpdate.Content;
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }

    private async Task<string> StreamMessageOutputFromKernelAsync(Kernel kernel, string prompt)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in kernel.InvokePromptStreamingAsync<StreamingChatMessageContent>(prompt))
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}");
                roleWritten = true;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                fullMessage += chatUpdate.Content;
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine("\n------------------------");
        return fullMessage;
    }
}
