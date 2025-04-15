// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Azure.AI.Inference;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate different ways of using streaming chat completion with Azure Foundry or GitHub models.
/// Azure AI Foundry: https://ai.azure.com/explore/models
/// GitHub Models: https://github.com/marketplace?type=models
/// </summary>
public class AzureAIInference_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates chat completion streaming using OpenAI.
    /// </summary>
    [Fact]
    public Task StreamChatAsync()
    {
        Console.WriteLine("======== Azure AI Inference - Chat Completion Streaming ========");

        var chatService = new ChatCompletionsClient(
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                credential: new Azure.AzureKeyCredential(TestConfiguration.AzureAIInference.ApiKey!))
            .AsIChatClient(TestConfiguration.AzureAIInference.ChatModelId)
            .AsChatCompletionService();

        return this.StartStreamingChatAsync(chatService);
    }

    /// <summary>
    /// This example demonstrates chat completion streaming using OpenAI via the kernel.
    /// </summary>
    [Fact]
    public async Task StreamChatPromptAsync()
    {
        Console.WriteLine("======== Azure AI Inference - Chat Prompt Completion Streaming ========");

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddAzureAIInferenceChatCompletion(
                modelId: TestConfiguration.AzureAIInference.ChatModelId,
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                apiKey: TestConfiguration.AzureAIInference.ApiKey)
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
        Console.WriteLine("======== Stream Text from Chat Content ========");

        // Create chat completion service
        var chatService = new ChatCompletionsClient(
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                credential: new Azure.AzureKeyCredential(TestConfiguration.AzureAIInference.ApiKey!))
            .AsIChatClient(TestConfiguration.AzureAIInference.ChatModelId)
            .AsChatCompletionService();

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

    /// <summary>
    /// Starts streaming chat with the chat completion service.
    /// </summary>
    /// <param name="chatCompletionService">The chat completion service instance.</param>
    private async Task StartStreamingChatAsync(IChatCompletionService chatCompletionService)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        OutputLastMessage(chatHistory);

        // Second assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);
    }

    /// <summary>
    /// Outputs the chat history by streaming the message output from the kernel.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="prompt">The prompt message.</param>
    /// <returns>The full message output from the kernel.</returns>
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
