// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;
using Xunit.Abstractions;

namespace MistralAI;

/// <summary>
/// Demonstrates the use of chat prompts with MistralAI.
/// </summary>
public sealed class MistralAI_Chat_Prompt : BaseTest
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

    public MistralAI_Chat_Prompt(ITestOutputHelper output) : base(output) { }
}
