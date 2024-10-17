﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using OllamaSharp.Models.Chat;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with Ollama Chat Completion API
public class Ollama_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Demonstrates how you can use the chat completion service directly.
    /// </summary>
    [Fact]
    public async Task ServicePromptAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("======== Ollama - Chat Completion ========");

        var chatService = new OllamaChatCompletionService(
            endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
            modelId: TestConfiguration.Ollama.ModelId);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        this.OutputLastMessage(chatHistory);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        this.OutputLastMessage(chatHistory);

        // Second assistant message
        reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        this.OutputLastMessage(chatHistory);
    }

    /// <summary>
    /// Demonstrates how you can get extra information from the service response, using the underlying inner content.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    [Fact]
    public async Task ServicePromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("======== Ollama - Chat Completion ========");

        var chatService = new OllamaChatCompletionService(
            endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
            modelId: TestConfiguration.Ollama.ModelId);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatService.GetChatMessageContentAsync(chatHistory);

        // Assistant message details
        // Ollama Sharp does not support non-streaming and always perform streaming calls, for this reason, the inner content is always a list of chunks.
        var replyInnerContent = reply.InnerContent as List<ChatResponseStream>;

        OutputInnerContent(replyInnerContent!);
    }

    /// <summary>
    /// Demonstrates how you can template a chat history call using the kernel for invocation.
    /// </summary>
    [Fact]
    public async Task ChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatCompletion(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint ?? "http://localhost:11434"),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

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
    public async Task ChatPromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatCompletion(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint ?? "http://localhost:11434"),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var functionResult = await kernel.InvokePromptAsync(chatPrompt.ToString());

        // Ollama Sharp does not support non-streaming and always perform streaming calls, for this reason, the inner content of a non-streaming result is a list of the generated chunks.
        var messageContent = functionResult.GetValue<ChatMessageContent>(); // Retrieves underlying chat message content from FunctionResult.
        var replyInnerContent = messageContent!.InnerContent as List<ChatResponseStream>; // Retrieves inner content from ChatMessageContent.

        OutputInnerContent(replyInnerContent!);
    }

    /// <summary>
    /// Retrieve extra information from each streaming chunk response in a list of chunks.
    /// </summary>
    /// <param name="innerContent">List of streaming chunks provided as inner content of a chat message</param>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    private void OutputInnerContent(List<ChatResponseStream> innerContent)
    {
        Console.WriteLine($"Model: {innerContent![0].Model}"); // Model doesn't change per chunk, so we can get it from the first chunk only
        Console.WriteLine(" -- Chunk changing data -- ");

        innerContent.ForEach(streamChunk =>
        {
            Console.WriteLine($"Message role: {streamChunk.Message.Role}");
            Console.WriteLine($"Message content: {streamChunk.Message.Content}");
            Console.WriteLine($"Created at: {streamChunk.CreatedAt}");
            Console.WriteLine($"Done: {streamChunk.Done}");
            /// The last message in the chunk is a <see cref="ChatDoneResponseStream"/> type with additional metadata.
            if (streamChunk is ChatDoneResponseStream doneStreamChunk)
            {
                Console.WriteLine($"Done Reason: {doneStreamChunk.DoneReason}");
                Console.WriteLine($"Eval count: {doneStreamChunk.EvalCount}");
                Console.WriteLine($"Eval duration: {doneStreamChunk.EvalDuration}");
                Console.WriteLine($"Load duration: {doneStreamChunk.LoadDuration}");
                Console.WriteLine($"Total duration: {doneStreamChunk.TotalDuration}");
                Console.WriteLine($"Prompt eval count: {doneStreamChunk.PromptEvalCount}");
                Console.WriteLine($"Prompt eval duration: {doneStreamChunk.PromptEvalDuration}");
            }
            Console.WriteLine("------------------------");
        });
    }
}
