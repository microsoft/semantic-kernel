// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

/**
 * The following example shows how to use Semantic Kernel with multiple streaming chat completion results.
 */
// ReSharper disable once InconsistentNaming
public static class Example45_MultiStreamingChatCompletion
{
    // First procress multiple Azure OpenAI chat completions
    // and then multiple plain OpenAI chat completions.
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiStreamingChatCompletionAsync();
        await OpenAIMultiStreamingChatCompletionAsync();
    }

    private static async Task AzureOpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completions - Raw Streaming ========");

        AzureOpenAIChatCompletionService chatCompletionService = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.ChatModelId,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await StreamingChatCompletionAsync(chatCompletionService, 3);
    }

    private static async Task OpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== OpenAI - Multiple Chat Completions - Raw Streaming ========");

        OpenAIChatCompletionService chatCompletionService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        await StreamingChatCompletionAsync(chatCompletionService, 3);
    }

    /// <summary>
    /// Streams the results of a chat completion request to the console.
    /// </summary>
    /// <param name="chatCompletionService">Chat completion service to use</param>
    /// <param name="numResultsPerPrompt">Number of results to get for each chat completion request</param>
    private static async Task StreamingChatCompletionAsync(IChatCompletionService chatCompletionService,
                                                           int numResultsPerPrompt)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = numResultsPerPrompt
        };

        var consoleLinesPerResult = 10;

        ClearDisplayByAddingEmptyLines();

        var prompt = "Hi, I'm looking for 5 random title names for sci-fi books";

        await ProcessStreamAsyncEnumerableAsync(chatCompletionService, prompt, executionSettings, consoleLinesPerResult);

        Console.WriteLine();

        // Set cursor position to after displayed results
        Console.SetCursorPosition(0, executionSettings.ResultsPerPrompt * consoleLinesPerResult);

        Console.WriteLine();
    }

    /// <summary>
    /// Does the actual streaming and display of the chat completion.
    /// </summary>
    private static async Task ProcessStreamAsyncEnumerableAsync(IChatCompletionService chatCompletionService, string prompt,
                                                                OpenAIPromptExecutionSettings executionSettings, int consoleLinesPerResult)
    {
        var messagesPerChoice = new Dictionary<int, string>();
        var chatHistory = new ChatHistory(prompt);

        // For each chat completion update
        await foreach (StreamingChatMessageContent chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings))
        {
            // Set cursor position to the beginning of where this choice (i.e. this result of
            // a single multi-result request) is to be displayed.
            Console.SetCursorPosition(0, chatUpdate.ChoiceIndex * consoleLinesPerResult + 1);

            // The first time around, start choice text with role information
            if (!messagesPerChoice.ContainsKey(chatUpdate.ChoiceIndex))
            {
                messagesPerChoice[chatUpdate.ChoiceIndex] = $"Role: {chatUpdate.Role ?? new AuthorRole()}\n";
            }

            // Add latest completion bit, if any
            if (chatUpdate.Content is { Length: > 0 })
            {
                messagesPerChoice[chatUpdate.ChoiceIndex] += chatUpdate.Content;
            }

            // Overwrite what is currently in the console area for the updated choice
            Console.Write(messagesPerChoice[chatUpdate.ChoiceIndex]);
        }
    }

    /// <summary>
    /// Add enough new lines to clear the console window.
    /// </summary>
    private static void ClearDisplayByAddingEmptyLines()
    {
        for (int i = 0; i < Console.WindowHeight - 2; i++)
        {
            Console.WriteLine();
        }
    }
}
