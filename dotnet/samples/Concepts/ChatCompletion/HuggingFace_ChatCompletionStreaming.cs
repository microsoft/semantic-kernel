// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;

namespace ChatCompletion;

/// <summary>
/// This example shows a way of using Hugging Face connector with HuggingFace Text Generation Inference (TGI) API.
/// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
/// <list type="number">
/// <item>Install HuggingFace TGI via docker</item>
/// <item><c>docker run -d --gpus all --shm-size 1g -p 8080:80 -v "c:\temp\huggingface:/data" ghcr.io/huggingface/text-generation-inference:latest --model-id teknium/OpenHermes-2.5-Mistral-7B</c></item>
/// <item>Run the examples</item>
/// </list>
/// </summary>
public class HuggingFace_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Sample showing how to use <see cref="IChatCompletionService"/> directly with a <see cref="ChatHistory"/>.
    /// </summary>
    [Fact]
    public async Task UsingServiceStreamingWithHuggingFace()
    {
        Console.WriteLine($"======== HuggingFace - Chat Completion - {nameof(UsingServiceStreamingWithHuggingFace)} ========");

        // HuggingFace local HTTP server endpoint
        var endpoint = new Uri("http://localhost:8080"); // Update the endpoint if you chose a different port. (defaults to 8080)
        var modelId = "teknium/OpenHermes-2.5-Mistral-7B"; // Update the modelId if you chose a different model.

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: modelId,
                endpoint: endpoint)
            .Build();

        var chatService = kernel.GetRequiredService<IChatCompletionService>();

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
    /// This example shows how to setup LMStudio to use with the <see cref="Kernel"/> InvokeAsync (Non-Streaming).
    /// </summary>
    [Fact]
    public async Task UsingKernelStreamingWithHuggingFace()
    {
        Console.WriteLine($"======== HuggingFace - Chat Completion - {nameof(UsingKernelStreamingWithHuggingFace)} ========");

        var endpoint = new Uri("http://localhost:8080"); // Update the endpoint if you chose a different port. (defaults to 8080)
        var modelId = "teknium/OpenHermes-2.5-Mistral-7B"; // Update the modelId if you chose a different model.

        var kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: modelId,
                apiKey: null,
                endpoint: endpoint)
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new HuggingFacePromptExecutionSettings
        {
            TopP = 0.5f,
            MaxTokens = 1000,
        });

        await foreach (var word in kernel.InvokeStreamingAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." }))
        {
            Console.WriteLine(word);
        }
    }
}
