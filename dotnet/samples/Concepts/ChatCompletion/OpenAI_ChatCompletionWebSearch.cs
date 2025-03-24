// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate how to do web search with OpenAI Chat Completion
/// </summary>
/// <remarks>
/// Currently, web search is only supported with the following models:
/// <list type="bullet">
/// <item>gpt-4o-search-preview</item>
/// <item>gpt-4o-mini-search-preview</item>
/// </list>
/// </remarks>
public class OpenAI_ChatCompletioWebSearch(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UsingChatCompletionWithWebSearchEnabled()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        // Ensure you use a supported model
        var modelId = "gpt-4o-mini-search-preview";
        var settings = new OpenAIPromptExecutionSettings
        {
            WebSearchOptions = new ChatWebSearchOptions()
        };

        Console.WriteLine($"======== Open AI - {nameof(UsingChatCompletionWithWebSearchEnabled)} ========");

        OpenAIChatCompletionService chatService = new(modelId, TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var result = await chatService.GetChatMessageContentAsync("What are the top 3 trending news currently", settings);

        // To retrieve the new annotations property from the result we need to use access the OpenAI.Chat.ChatCompletion directly
        var chatCompletion = result.InnerContent as OpenAI.Chat.ChatCompletion;

        for (var i = 0; i < chatCompletion!.Annotations.Count; i++)
        {
            var annotation = chatCompletion!.Annotations[i];
            Console.WriteLine($"--- Annotation [{i + 1}] ---");
            Console.WriteLine($"Title: {annotation.WebResourceTitle}");
            Console.WriteLine($"Uri: {annotation.WebResourceUri}");
        }
    }
}
