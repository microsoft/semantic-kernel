// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace PromptTemplates;

public sealed class ChatLoopWithPrompt(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample demonstrates how to render a chat history to a
    /// prompt and use chat completion prompts in a loop.
    /// </summary>
    [Fact]
    public async Task ExecuteChatLoopAsPromptAsync()
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatHistory = new ChatHistory();
        KernelArguments arguments = new() { { "chatHistory", chatHistory } };

        string[] userMessages = [
            "What is Seattle?",
            "What is the population of Seattle?",
            "What is the area of Seattle?",
            "What is the weather in Seattle?",
            "What is the zip code of Seattle?",
            "What is the elevation of Seattle?",
            "What is the latitude of Seattle?",
            "What is the longitude of Seattle?",
            "What is the mayor of Seattle?"
        ];

        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessage(userMessage);
            OutputLastMessage(chatHistory);

            var function = kernel.CreateFunctionFromPrompt(
                new()
                {
                    Template =
                    """
                    {{#each (chatHistory)}}
                    <message role="{{Role}}">{{Content}}</message>
                    {{/each}}
                    """,
                    TemplateFormat = "handlebars"
                },
                new HandlebarsPromptTemplateFactory()
            );

            var response = await kernel.InvokeAsync(function, arguments);

            chatHistory.AddAssistantMessage(response.ToString());
            OutputLastMessage(chatHistory);
        }
    }
}
