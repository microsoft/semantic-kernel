// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Represents a class that demonstrates image-to-text functionality.
/// </summary>
public sealed class Example87_MistralAIChatCompletion : BaseTest
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
            WriteLine(message.Content);
        }
    }

    [Fact]
    public async Task ChatPromptAsync()
    {
        const string ChatPrompt = @"
            <message role=""system"">Respond in French.</message>
            <message role=""user"">What is the best French cheese?</message>
        ";

        var kernel = Kernel.CreateBuilder()
            .AddMistralChatCompletion(
                model: TestConfiguration.MistralAI.ChatModelId,
                apiKey: TestConfiguration.MistralAI.ApiKey)
            .Build();

        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, new MistralAIPromptExecutionSettings { MaxTokens = 500 });
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        WriteLine(chatPromptResult);
    }

    public Example87_MistralAIChatCompletion(ITestOutputHelper output) : base(output) { }
}
