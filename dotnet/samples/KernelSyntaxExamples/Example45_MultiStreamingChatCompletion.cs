// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// The following example shows how to use Semantic Kernel with multiple streaming chat completion results.
public class Example45_MultiStreamingChatCompletion : BaseTest
{
    [Fact]
    public Task AzureOpenAIMultiStreamingChatCompletionAsync()
    {
        WriteLine("======== Azure OpenAI - Multiple Chat Completions - Raw Streaming ========");

        AzureOpenAIChatCompletionService chatCompletionService = new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        return StreamingChatCompletionAsync(chatCompletionService, 3);
    }

    [Fact]
    public Task OpenAIMultiStreamingChatCompletionAsync()
    {
        WriteLine("======== OpenAI - Multiple Chat Completions - Raw Streaming ========");

        OpenAIChatCompletionService chatCompletionService = new(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        return StreamingChatCompletionAsync(chatCompletionService, 3);
    }

    /// <summary>
    /// Streams the results of a chat completion request to the console.
    /// </summary>
    /// <param name="chatCompletionService">Chat completion service to use</param>
    /// <param name="numResultsPerPrompt">Number of results to get for each chat completion request</param>
    private async Task StreamingChatCompletionAsync(IChatCompletionService chatCompletionService,
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

        // Uncomment this if you want to use a console app to display the results
        // ClearDisplayByAddingEmptyLines();

        var prompt = "Hi, I'm looking for 5 random title names for sci-fi books";

        await ProcessStreamAsyncEnumerableAsync(chatCompletionService, prompt, executionSettings, consoleLinesPerResult);

        WriteLine();

        // Set cursor position to after displayed results
        // Console.SetCursorPosition(0, executionSettings.ResultsPerPrompt * consoleLinesPerResult);

        WriteLine();
    }

    /// <summary>
    /// Does the actual streaming and display of the chat completion.
    /// </summary>
    private async Task ProcessStreamAsyncEnumerableAsync(IChatCompletionService chatCompletionService, string prompt,
                                                                OpenAIPromptExecutionSettings executionSettings, int consoleLinesPerResult)
    {
        var messagesPerChoice = new Dictionary<int, string>();
        var chatHistory = new ChatHistory(prompt);

        // For each chat completion update
        await foreach (StreamingChatMessageContent chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings))
        {
            // Set cursor position to the beginning of where this choice (i.e. this result of
            // a single multi-result request) is to be displayed.
            // Console.SetCursorPosition(0, chatUpdate.ChoiceIndex * consoleLinesPerResult + 1);

            // The first time around, start choice text with role information
            if (!messagesPerChoice.ContainsKey(chatUpdate.ChoiceIndex))
            {
                messagesPerChoice[chatUpdate.ChoiceIndex] = $"Role: {chatUpdate.Role ?? new AuthorRole()}\n";
                Write($"Choice index: {chatUpdate.ChoiceIndex}, Role: {chatUpdate.Role ?? new AuthorRole()}");
            }

            // Add latest completion bit, if any
            if (chatUpdate.Content is { Length: > 0 })
            {
                messagesPerChoice[chatUpdate.ChoiceIndex] += chatUpdate.Content;
            }

            // Overwrite what is currently in the console area for the updated choice
            // Console.Write(messagesPerChoice[chatUpdate.ChoiceIndex]);
            Write($"Choice index: {chatUpdate.ChoiceIndex}, Content: {chatUpdate.Content}");
        }

        // Display the aggregated results
        foreach (string message in messagesPerChoice.Values)
        {
            WriteLine("-------------------");
            WriteLine(message);
        }
    }

    /// <summary>
    /// Add enough new lines to clear the console window.
    /// </summary>
    private void ClearDisplayByAddingEmptyLines()
    {
        for (int i = 0; i < Console.WindowHeight - 2; i++)
        {
            WriteLine();
        }
    }

    public Example45_MultiStreamingChatCompletion(ITestOutputHelper output) : base(output)
    {
    }
}
