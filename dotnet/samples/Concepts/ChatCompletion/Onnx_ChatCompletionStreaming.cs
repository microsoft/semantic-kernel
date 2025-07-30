// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate the ways different content types are streamed by Onnx GenAI via the chat completion service.
/// </summary>
public class Onnx_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Streaming chat completion streaming using the service directly.
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>ModelId:</term>
    /// <description>phi-3</description>
    /// </item>
    /// <item>
    /// <term>ModelPath:</term>
    /// <description>D:\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task StreamChatAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.ModelId);   // dotnet user-secrets set "Onnx:ModelId" "<model-id>"
        Assert.NotNull(TestConfiguration.Onnx.ModelPath); // dotnet user-secrets set "Onnx:ModelPath" "<model-folder-path>"

        Console.WriteLine("======== Onnx - Chat Completion Streaming ========");

        using var chatService = new OnnxRuntimeGenAIChatCompletionService(
            modelId: TestConfiguration.Onnx.ModelId,
            modelPath: TestConfiguration.Onnx.ModelPath);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        await StreamMessageOutputAsync(chatService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        OutputLastMessage(chatHistory);

        // Second assistant message
        await StreamMessageOutputAsync(chatService, chatHistory, AuthorRole.Assistant);
    }

    /// <summary>
    /// Streaming chat completion using the kernel.
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>ModelId:</term>
    /// <description>phi-3</description>
    /// </item>
    /// <item>
    /// <term>ModelPath:</term>
    /// <description>D:\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task StreamChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.ModelId);   // dotnet user-secrets set "Onnx:ModelId" "<model-id>"
        Assert.NotNull(TestConfiguration.Onnx.ModelPath); // dotnet user-secrets set "Onnx:ModelPath" "<model-folder-path>"

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        Console.WriteLine("======== Onnx - Chat Completion Streaming ========");

        var kernel = Kernel.CreateBuilder()
            .AddOnnxRuntimeGenAIChatCompletion(
                serviceId: "onnx",
                modelId: TestConfiguration.Onnx.ModelId,
                modelPath: TestConfiguration.Onnx.ModelPath)
            .Build();

        var reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());

        Console.WriteLine(reply);

        DisposeServices(kernel);
    }

    /// <summary>
    /// This example demonstrates how the chat completion service streams text content.
    /// It shows how to access the response update via StreamingChatMessageContent.Content property
    /// and alternatively via the StreamingChatMessageContent.Items property.
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>ModelId:</term>
    /// <description>phi-3</description>
    /// </item>
    /// <item>
    /// <term>ModelPath:</term>
    /// <description>D:\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task StreamTextFromChatAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.ModelId);   // dotnet user-secrets set "Onnx:ModelId" "<model-id>"
        Assert.NotNull(TestConfiguration.Onnx.ModelPath); // dotnet user-secrets set "Onnx:ModelPath" "<model-folder-path>"

        Console.WriteLine("======== Stream Text from Chat Content ========");

        // Create chat completion service
        using var chatService = new OnnxRuntimeGenAIChatCompletionService(
            modelId: TestConfiguration.Onnx.ModelId,
            modelPath: TestConfiguration.Onnx.ModelPath);

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

    private async Task StreamMessageOutputAsync(OnnxRuntimeGenAIChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
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
    /// To avoid any potential memory leak all disposable services created by the kernel are disposed.
    /// </summary>
    /// <param name="kernel">Target kernel</param>
    private static void DisposeServices(Kernel kernel)
    {
        foreach (var target in kernel
            .GetAllServices<IChatCompletionService>()
            .OfType<IDisposable>())
        {
            target.Dispose();
        }
    }
}
