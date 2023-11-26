// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example45_MultiStreamingChatCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiStreamingChatCompletionAsync();
        await OpenAIMultiStreamingChatCompletionAsync();
    }

    private static async Task AzureOpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion - Raw Streaming ========");

        AzureOpenAIChatCompletion azureOpenAIChatCompletion = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await StreamingChatCompletionAsync(azureOpenAIChatCompletion);
    }

    private static async Task OpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion - Raw Streaming ========");

        OpenAIChatCompletion openAIChatCompletion = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        await StreamingChatCompletionAsync(openAIChatCompletion);
    }

    private static async Task StreamingChatCompletionAsync(IChatCompletion chatCompletion)
    {
        var requestSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 3
        };

        var consoleLinesPerResult = 10;

        PrepareDisplay();
        var prompt = "Hi, I'm looking for 5 random title names for sci-fi books";
        await ProcessStreamAsyncEnumerableAsync(chatCompletion, prompt, requestSettings, consoleLinesPerResult);

        Console.WriteLine();

        Console.SetCursorPosition(0, requestSettings.ResultsPerPrompt * consoleLinesPerResult);
        Console.WriteLine();
    }

    private static async Task ProcessStreamAsyncEnumerableAsync(IChatCompletion chatCompletion, string prompt, OpenAIPromptExecutionSettings requestSettings, int consoleLinesPerResult)
    {
        var roleDisplayed = new List<int>();
        var messagePerChoice = new Dictionary<int, string>();
        await foreach (var chatUpdate in chatCompletion.GetStreamingContentAsync<StreamingChatContent>(prompt, requestSettings))
        {
            string newContent = string.Empty;
            Console.SetCursorPosition(0, chatUpdate.ChoiceIndex * consoleLinesPerResult);
            if (!roleDisplayed.Contains(chatUpdate.ChoiceIndex) && chatUpdate.Role.HasValue)
            {
                newContent = $"Role: {chatUpdate.Role.Value}\n";
                roleDisplayed.Add(chatUpdate.ChoiceIndex);
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                newContent += chatUpdate.Content;
            }

            if (!messagePerChoice.ContainsKey(chatUpdate.ChoiceIndex))
            {
                messagePerChoice.Add(chatUpdate.ChoiceIndex, string.Empty);
            }
            messagePerChoice[chatUpdate.ChoiceIndex] += newContent;

            Console.Write(messagePerChoice[chatUpdate.ChoiceIndex]);
        }
    }

    /// <summary>
    /// Break enough lines as the current console window size to display the results
    /// </summary>
    private static void PrepareDisplay()
    {
        for (int i = 0; i < Console.WindowHeight - 2; i++)
        {
            Console.WriteLine();
        }
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }
}
