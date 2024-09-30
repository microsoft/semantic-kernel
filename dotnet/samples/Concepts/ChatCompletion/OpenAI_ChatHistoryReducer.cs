// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
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
    public async Task ShowHowToReduceChatHistoryToLastMessageAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.WithChatHistoryReducer(ChatHistoryLastMessageReducerAsync);

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
    public async Task ShowHowToReduceChatHistoryToLastMessageStreamingAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.WithChatHistoryReducer(ChatHistoryLastMessageReducerAsync);

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

    [Fact]
    public async Task ShowHowToReduceChatHistoryToMaxTokensAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.WithChatHistoryReducer(ChatHistoryMaxTokensReducerAsync);

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessageWithTokenCount("You are an expert on the best restaurants in the world. Keep responses short.");

        string[] userMessages = [
            "Recommend restaurants in Seattle",
            "What is the best Italian restaurant?",
            "What is the best Korean restaurant?",
            "Recommend restaurants in Dublin",
            "What is the best Indian restaurant?",
            "What is the best Japanese restaurant?",
        ];

        int totalTokenCount = 0;
        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessageWithTokenCount(userMessage);
            Console.WriteLine($"\n>>> User:\n{userMessage}");

            var response = await chatService.GetChatMessageContentAsync(chatHistory);
            chatHistory.AddAssistantMessageWithTokenCount(response.Content!);
            Console.WriteLine($"\n>>> Assistant:\n{response.Content!}");

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokens ?? 0;
            }
        }

        // Example total token usage is approximately: 3000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }

    #region private
    private const int MaxTokenCount = 100;

    /// <summary>
    /// ChatHistoryReducer function that just preserves the system message and the last n messages.
    /// </summary>
    private static async Task<ChatHistory?> ChatHistoryLastMessageReducerAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var systemMessage = GetSystemMessage(chatHistory);
        ChatHistory reducedChatHistory = systemMessage is not null ? new(systemMessage.Content!) : new();
        // Using the last message only but could be the last N messages
        reducedChatHistory.Add(chatHistory[^1]);
        return reducedChatHistory;
    }

    /// <summary>
    /// ChatHistoryReducer function that just preserves the system message and the last n messages.
    /// </summary>
    private static async Task<ChatHistory?> ChatHistoryMaxTokensReducerAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        ChatHistory reducedChatHistory = [];
        var totalTokenCount = 0;
        var insertIndex = 0;
        var systemMessage = GetSystemMessage(chatHistory);
        if (systemMessage is not null)
        {
            reducedChatHistory.Add(systemMessage);
            totalTokenCount += (int)(systemMessage.Metadata?["TokenCount"] ?? 0);
            insertIndex = 1;
        }
        // Add the remaining messages that fit within the token limit
        for (int i = chatHistory.Count - 1; i >= 1; i--)
        {
            var tokenCount = (int)(chatHistory[i].Metadata?["TokenCount"] ?? 0);
            if (tokenCount + totalTokenCount > MaxTokenCount)
            {
                break;
            }
            reducedChatHistory.Insert(insertIndex, chatHistory[i]);
            totalTokenCount += tokenCount;
        }
        return reducedChatHistory;
    }

    /// <summary>
    /// ChatHistoryReducer function that summarizes as.
    /// </summary>
    private static async Task<ChatHistory?> ChatHistorySummarizingReducerAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var systemMessage = GetSystemMessage(chatHistory);
        ChatHistory reducedChatHistory = systemMessage is not null ? new(systemMessage.Content!) : new();
        // Using the last message only but could be the last N messages
        reducedChatHistory.Add(chatHistory[^1]);
        return reducedChatHistory;
    }

    /// <summary>
    /// Returns the system prompt from the chat history.
    /// </summary>
    private static ChatMessageContent? GetSystemMessage(ChatHistory chatHistory)
    {
        return chatHistory.FirstOrDefault(m => m.Role == AuthorRole.System);
    }
    #endregion
}
