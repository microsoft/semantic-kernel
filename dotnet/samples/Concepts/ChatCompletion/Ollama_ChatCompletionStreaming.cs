// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using OllamaSharp;
using OllamaSharp.Models.Chat;

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

        using var ollamaClient = new OllamaApiClient(
            uriString: TestConfiguration.Ollama.Endpoint,
            defaultModel: TestConfiguration.Ollama.ModelId);

        var chatService = ollamaClient.AsChatCompletionService();

        return this.StartStreamingChatAsync(chatService);
    }

    /// <summary>
    /// This example demonstrates retrieving extra information chat completion streaming using Ollama.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    [Fact]
    public async Task StreamChatWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("======== Ollama - Chat Completion Streaming ========");

        using var ollamaClient = new OllamaApiClient(
            uriString: TestConfiguration.Ollama.Endpoint,
            defaultModel: TestConfiguration.Ollama.ModelId);

        var chatService = ollamaClient.AsChatCompletionService();

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        this.OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        await foreach (var chatUpdate in chatService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            var innerContent = chatUpdate.InnerContent as ChatResponseStream;
            OutputInnerContent(innerContent!);
        }
    }

    /// <summary>
    /// Demonstrates how you can template a chat history call while using the kernel for invocation.
    /// </summary>
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
    /// Demonstrates how you can template a chat history call and get extra information from the response while using the kernel for invocation.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    [Fact]
    public async Task StreamChatPromptWithInnerContentAsync()
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

        await foreach (var chatUpdate in kernel.InvokePromptStreamingAsync<StreamingChatMessageContent>(chatPrompt.ToString()))
        {
            var innerContent = chatUpdate.InnerContent as ChatResponseStream;
            OutputInnerContent(innerContent!);
        }
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

        using var ollamaClient = new OllamaApiClient(
            uriString: TestConfiguration.Ollama.Endpoint,
            defaultModel: TestConfiguration.Ollama.ModelId);

        // Create chat completion service
        var chatService = ollamaClient.AsChatCompletionService();

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

    /// <summary>
    /// Retrieve extra information from each streaming chunk response.
    /// </summary>
    /// <param name="streamChunk">Streaming chunk provided as inner content of a streaming chat message</param>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    private void OutputInnerContent(ChatResponseStream streamChunk)
    {
        Console.WriteLine($"Model: {streamChunk.Model}");
        Console.WriteLine($"Message role: {streamChunk.Message.Role}");
        Console.WriteLine($"Message content: {streamChunk.Message.Content}");
        Console.WriteLine($"Created at: {streamChunk.CreatedAt}");
        Console.WriteLine($"Done: {streamChunk.Done}");

        /// The last message in the chunk is a <see cref="ChatDoneResponseStream"/> type with additional metadata.
        if (streamChunk is ChatDoneResponseStream doneStream)
        {
            Console.WriteLine($"Done Reason: {doneStream.DoneReason}");
            Console.WriteLine($"Eval count: {doneStream.EvalCount}");
            Console.WriteLine($"Eval duration: {doneStream.EvalDuration}");
            Console.WriteLine($"Load duration: {doneStream.LoadDuration}");
            Console.WriteLine($"Total duration: {doneStream.TotalDuration}");
            Console.WriteLine($"Prompt eval count: {doneStream.PromptEvalCount}");
            Console.WriteLine($"Prompt eval duration: {doneStream.PromptEvalDuration}");
        }
        Console.WriteLine("------------------------");
    }
}
