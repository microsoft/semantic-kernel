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
public class LMStudio_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example shows how to setup LMStudio to use with the <see cref="Kernel"/> InvokeAsync (Non-Streaming).
    /// </summary>
    [Fact]
#pragma warning restore CS0419 // Ambiguous reference in cref attribute
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

        var response = await kernel.InvokeAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." });
        Console.WriteLine(response);
    }

    /// <summary>
    /// Sample showing how to use <see cref="IChatCompletionService"/> directly with a <see cref="ChatHistory"/>.
    /// </summary>
    [Fact]
    public async Task UsingServiceNonStreamingWithLMStudio()
    {
        Console.WriteLine($"======== LM Studio - Chat Completion - {nameof(UsingServiceNonStreamingWithLMStudio)} ========");

        var modelId = "llama-2-7b-chat"; // Update the modelId if you chose a different model.
        var endpoint = new Uri("http://localhost:1234/v1"); // Update the endpoint if you chose a different port.

        OpenAIChatCompletionService chatService = new(modelId: modelId, apiKey: null, endpoint: endpoint);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        OutputLastMessage(chatHistory);

        // Second assistant message
        reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);
    }
}
