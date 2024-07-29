// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;

namespace ChatCompletion;

/// <summary>
/// Demonstrates the use of chat prompts with MistralAI.
/// </summary>
public sealed class MistralAI_ChatPrompt(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GetChatMessageContentsAsync()
    {
        var service = new MistralAIChatCompletionService(
            TestConfiguration.MistralAI.ChatModelId!,
            TestConfiguration.MistralAI.ApiKey!
        );

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Respond in French."),
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(
            chatHistory, new MistralAIPromptExecutionSettings { MaxTokens = 500 });

        foreach (var message in response)
        {
            Console.WriteLine(message.Content);
        }
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsync()
    {
        var service = new MistralAIChatCompletionService(
            TestConfiguration.MistralAI.ChatModelId!,
            TestConfiguration.MistralAI.ApiKey!
        );

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Respond in French."),
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var streamingChat = service.GetStreamingChatMessageContentsAsync(
            chatHistory, new MistralAIPromptExecutionSettings { MaxTokens = 500 });

        await foreach (var update in streamingChat)
        {
            Console.Write(update);
        }
    }

    [Fact]
    public async Task ChatPromptAsync()
    {
        const string ChatPrompt = """
            <message role="system">Respond in French.</message>
            <message role="user">What is the best French cheese?</message>
        """;

        var kernel = Kernel.CreateBuilder()
            .AddMistralChatCompletion(
                modelId: TestConfiguration.MistralAI.ChatModelId,
                apiKey: TestConfiguration.MistralAI.ApiKey)
            .Build();

        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, new MistralAIPromptExecutionSettings { MaxTokens = 500 });
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        Console.WriteLine(chatPromptResult);
    }
}
