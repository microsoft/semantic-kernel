// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Azure.AI.Inference;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate different ways of using chat completion with Azure Foundry or GitHub models.
/// Azure AI Foundry: https://ai.azure.com/explore/models
/// GitHub Models: https://github.com/marketplace?type=models
/// </summary>
public class AzureAIInference_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ServicePromptAsync()
    {
        Console.WriteLine("======== Azure AI Inference - Chat Completion ========");

        Assert.NotNull(TestConfiguration.AzureAIInference.ApiKey);

        var chatService = new ChatCompletionsClient(
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                credential: new Azure.AzureKeyCredential(TestConfiguration.AzureAIInference.ApiKey))
            .AsIChatClient(TestConfiguration.AzureAIInference.ChatModelId)
            .AsChatCompletionService();

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

        /* Output:

        Chat content:
        ------------------------
        System: You are a librarian, expert about books
        ------------------------
        User: Hi, I'm looking for book suggestions
        ------------------------
        Assistant: Sure, I'd be happy to help! What kind of books are you interested in? Fiction or non-fiction? Any particular genre?
        ------------------------
        User: I love history and philosophy, I'd like to learn something new about Greece, any suggestion?
        ------------------------
        Assistant: Great! For history and philosophy books about Greece, here are a few suggestions:

        1. "The Greeks" by H.D.F. Kitto - This is a classic book that provides an overview of ancient Greek history and culture, including their philosophy, literature, and art.

        2. "The Republic" by Plato - This is one of the most famous works of philosophy in the Western world, and it explores the nature of justice and the ideal society.

        3. "The Peloponnesian War" by Thucydides - This is a detailed account of the war between Athens and Sparta in the 5th century BCE, and it provides insight into the political and military strategies of the time.

        4. "The Iliad" by Homer - This epic poem tells the story of the Trojan War and is considered one of the greatest works of literature in the Western canon.

        5. "The Histories" by Herodotus - This is a comprehensive account of the Persian Wars and provides a wealth of information about ancient Greek culture and society.

        I hope these suggestions are helpful!
        ------------------------
        */
    }

    [Fact]
    public async Task ChatPromptAsync()
    {
        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddAzureAIInferenceChatCompletion(
                modelId: TestConfiguration.AzureAIInference.ChatModelId,
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                apiKey: TestConfiguration.AzureAIInference.ApiKey)
            .Build();

        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        Console.WriteLine(reply);
    }
}
