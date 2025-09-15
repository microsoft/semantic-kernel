// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// This example shows a way of using OpenAI connector with other APIs that supports the same ChatCompletion API standard from OpenAI.
/// <list type="number">
/// <item>Install LMStudio Platform in your environment (As of now: 0.3.10)</item>
/// <item>Open LM Studio</item>
/// <item>Search and Download Llama2 model or any other</item>
/// <item>Update the modelId parameter with the model llm name loaded (i.e: llama-2-7b-chat)</item>
/// <item>Start the Local Server on http://localhost:1234</item>
/// <item>Run the examples</item>
/// </list>
/// </summary>
public class LMStudio_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Sample showing how to use <see cref="IChatCompletionService"/> streaming directly with a <see cref="ChatHistory"/>.
    /// </summary>
    [Fact]
    public async Task UsingServiceStreamingWithLMStudio()
    {
        Console.WriteLine($"======== LM Studio - Chat Completion - {nameof(UsingServiceStreamingWithLMStudio)} ========");

        var modelId = "llama-2-7b-chat"; // Update the modelId if you chose a different model.
        var endpoint = new Uri("http://localhost:1234/v1"); // Update the endpoint if you chose a different port.

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                apiKey: null,
                endpoint: endpoint)
            .Build();

        OpenAIChatCompletionService chatCompletionService = new(modelId: modelId, apiKey: null, endpoint: endpoint);

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
    /// This example shows how to setup LMStudio to use with the Kernel InvokeAsync (Streaming).
    /// </summary>
    [Fact]
    public async Task UsingKernelStreamingWithLMStudio()
    {
        Console.WriteLine($"======== LM Studio - Chat Completion - {nameof(UsingKernelStreamingWithLMStudio)} ========");

        var modelId = "llama-2-7b-chat"; // Update the modelId if you chose a different model.
        var endpoint = new Uri("http://localhost:1234/v1"); // Update the endpoint if you chose a different port.

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                apiKey: null,
                endpoint: endpoint)
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            TopP = 0.5,
            MaxTokens = 1000,
        });

        await foreach (var word in kernel.InvokeStreamingAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." }))
        {
            Console.WriteLine(word);
        }
    }
}
