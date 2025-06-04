// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

/// <summary>
/// The sample show how to add a chat history reducer which only sends the last two messages in <see cref="ChatHistory"/> to the model.
/// </summary>
public class MultipleProviders_ChatHistoryReducer(ITestOutputHelper output) : BaseTest(output)
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
            Console.WriteLine($"\n>>> Assistant:\n{response.Content!}");

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokenCount ?? 0;
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

        var truncatedSize = 2; // keep system message and last user message only
        IChatCompletionService chatService = openAiChatService.UsingChatHistoryReducer(new ChatHistoryTruncationReducer(truncatedSize));

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
            Console.WriteLine($"\n>>> User:\n{userMessage}");

            var response = await chatService.GetChatMessageContentAsync(chatHistory);
            chatHistory.AddAssistantMessage(response.Content!);
            Console.WriteLine($"\n>>> Assistant:\n{response.Content!}");

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokenCount ?? 0;
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

        var truncatedSize = 2; // keep system message and last user message only
        IChatCompletionService chatService = openAiChatService.UsingChatHistoryReducer(new ChatHistoryTruncationReducer(truncatedSize));

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
            Console.WriteLine($"\n>>> User:\n{userMessage}");

            var response = new StringBuilder();
            var chatUpdates = chatService.GetStreamingChatMessageContentsAsync(chatHistory);
            await foreach (var chatUpdate in chatUpdates)
            {
                response.Append((string?)chatUpdate.Content);

                if (chatUpdate.InnerContent is StreamingChatCompletionUpdate openAiChatUpdate)
                {
                    totalTokenCount += openAiChatUpdate.Usage?.TotalTokenCount ?? 0;
                }
            }
            chatHistory.AddAssistantMessage(response.ToString());
            Console.WriteLine($"\n>>> Assistant:\n{response}");
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
        IChatCompletionService chatService = openAiChatService.UsingChatHistoryReducer(new ChatHistoryMaxTokensReducer(100));

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
                totalTokenCount += chatCompletion.Usage?.TotalTokenCount ?? 0;
            }
        }

        // Example total token usage is approximately: 3000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }

    [Fact]
    public async Task ShowHowToReduceChatHistoryWithSummarizationAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        OpenAIChatCompletionService openAiChatService = new(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        IChatCompletionService chatService = openAiChatService.UsingChatHistoryReducer(new ChatHistorySummarizationReducer(openAiChatService, 2, 4));

        var chatHistory = new ChatHistory("You are an expert on the best restaurants in every city. Answer for the city the user has asked about.");

        string[] userMessages = [
            "Recommend restaurants in Seattle",
            "What is the best Italian restaurant?",
            "What is the best Korean restaurant?",
            "What is the best Brazilian restaurant?",
            "Recommend restaurants in Dublin",
            "What is the best Indian restaurant?",
            "What is the best Japanese restaurant?",
            "What is the best French restaurant?",

        ];

        int totalTokenCount = 0;
        foreach (var userMessage in userMessages)
        {
            chatHistory.AddUserMessage(userMessage);
            Console.WriteLine($"\n>>> User:\n{userMessage}");

            var response = await chatService.GetChatMessageContentAsync(chatHistory);
            chatHistory.AddAssistantMessage(response.Content!);
            Console.WriteLine($"\n>>> Assistant:\n{response.Content!}");

            if (response.InnerContent is OpenAI.Chat.ChatCompletion chatCompletion)
            {
                totalTokenCount += chatCompletion.Usage?.TotalTokenCount ?? 0;
            }
        }

        // Example total token usage is approximately: 3000
        Console.WriteLine($"Total Token Count: {totalTokenCount}");
    }
}
