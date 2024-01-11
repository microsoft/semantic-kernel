// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
public class Example44_MultiChatCompletion : BaseTest
{
    [Fact]
    public Task AzureOpenAIMultiChatCompletionAsync()
    {
        WriteLine("======== Azure OpenAI - Multiple Chat Completion ========");

        AzureOpenAIChatCompletionService chatCompletionService = new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        return RunChatAsync(chatCompletionService);
    }

    [Fact]
    public Task OpenAIMultiChatCompletionAsync()
    {
        WriteLine("======== Open AI - Multiple Chat Completion ========");

        OpenAIChatCompletionService chatCompletionService = new(modelId: TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        return RunChatAsync(chatCompletionService);
    }

    private async Task RunChatAsync(IChatCompletionService chatCompletionService)
    {
        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");
        await MessageOutputAsync(chatHistory);

        var chatExecutionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0,
        };

        // First bot assistant message
        foreach (var chatMessageChoice in await chatCompletionService.GetChatMessageContentsAsync(chatHistory, chatExecutionSettings))
        {
            chatHistory.Add(chatMessageChoice!);
            await MessageOutputAsync(chatHistory);
        }

        WriteLine();
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        WriteLine($"{message.Role}: {message.Content}");
        WriteLine("------------------------");

        return Task.CompletedTask;
    }

    public Example44_MultiChatCompletion(ITestOutputHelper output) : base(output)
    {
    }
}
