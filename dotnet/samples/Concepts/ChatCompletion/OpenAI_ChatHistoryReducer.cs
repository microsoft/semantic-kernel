// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

/// <summary>
/// The sample show how to add a chat history reducer which only sends the last two messages in <see cref="ChatHistory"/> to the model.
/// </summary>
public class OpenAI_ChatHistoryReducer(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ShowTotalTokenCountAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        var chatHistory = new ChatHistory("You are a librarian and expert on books about cities");

        string[] userMessages = [
            "Recommend a list of books about Seattle",
            "Recommend a list of books about Dublin",
            "Recommend a list of books about Amsterdam",
            "Recommend a list of books about Paris",
            "Recommend a list of books about London"
        ];

        int totalTokenCount = 0;
        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessage(userMessage);

            var response = await openAiChatService.GetChatMessageContentAsync(chatHistory);
            chatHistory.AddAssistantMessage(response.Content!);

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokens ?? 0;
            }
        }

        // Example total token usage is approximately: 10000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }

    [Fact]
    public async Task ShowHowToReduceChatHistoryAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.WithChatHistoryReducer(ChatHistoryReducerAsync);

        var chatHistory = new ChatHistory("You are a librarian and expert on books about cities");

        string[] userMessages = [
            "Recommend a list of books about Seattle",
            "Recommend a list of books about Dublin",
            "Recommend a list of books about Amsterdam",
            "Recommend a list of books about Paris",
            "Recommend a list of books about London"
        ];

        int totalTokenCount = 0;
        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessage(userMessage);

            var response = await chatService.GetChatMessageContentAsync(chatHistory);
            chatHistory.AddAssistantMessage(response.Content!);

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokens ?? 0;
            }
        }

        // Example total token usage is approximately: 3000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }

    [Fact]
    public async Task ShowHowToReduceChatHistoryStreamingAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.WithChatHistoryReducer(ChatHistoryReducerAsync);

        var chatHistory = new ChatHistory("You are a librarian and expert on books about cities");

        string[] userMessages = [
            "Recommend a list of books about Seattle",
            "Recommend a list of books about Dublin",
            "Recommend a list of books about Amsterdam",
            "Recommend a list of books about Paris",
            "Recommend a list of books about London"
        ];

        int totalTokenCount = 0;
        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessage(userMessage);

            var response = new StringBuilder();
            var chatUpdates = chatService.GetStreamingChatMessageContentsAsync(chatHistory);
            await foreach (var chatUpdate in chatUpdates)
            {
                response.Append((string?)chatUpdate.Content);

                if (chatUpdate.InnerContent is StreamingChatCompletionUpdate openAiChatUpdate)
                {
                    totalTokenCount += openAiChatUpdate.Usage?.TotalTokens ?? 0;
                }
            }
            chatHistory.AddAssistantMessage(response.ToString());
        }

        // Example total token usage is approximately: 3000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }

    #region private
    /// <summary>
    /// ChatHistoryReducer function that just preserves the system message and the last message.
    /// </summary>
    private static async Task<ChatHistory?> ChatHistoryReducerAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var firstMessage = chatHistory.FirstOrDefault();
        ChatHistory? reducedChatHistory = (firstMessage?.Role == AuthorRole.System) ? new(firstMessage?.Content!) : new();
        reducedChatHistory.Add(chatHistory[^1]);
        return reducedChatHistory ?? chatHistory;
    }
    #endregion
}
