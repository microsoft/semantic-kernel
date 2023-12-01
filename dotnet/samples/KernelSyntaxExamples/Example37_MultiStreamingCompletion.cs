// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with streaming Multiple Results Chat Completion
 */
// ReSharper disable once InconsistentNaming
public static class Example37_MultiStreamingCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiChatCompletionStreamAsync();
        await OpenAIChatCompletionStreamAsync();
    }

    private static async Task AzureOpenAIMultiChatCompletionStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion - Raw Streaming ========");

        var chatCompletion = new AzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await ChatCompletionStreamAsync(chatCompletion);
    }

    private static async Task OpenAIChatCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion - Raw Streaming ========");

        ITextCompletion textCompletion = new OpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        await ChatCompletionStreamAsync(textCompletion);
    }

    private static async Task ChatCompletionStreamAsync(ITextCompletion textCompletion)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
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
        await ProcessStreamAsyncEnumerableAsync(textCompletion, prompt, executionSettings, consoleLinesPerResult);

        Console.WriteLine();

        Console.SetCursorPosition(0, executionSettings.ResultsPerPrompt * consoleLinesPerResult);
        Console.WriteLine();
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
    private static async Task ProcessStreamAsyncEnumerableAsync(ITextCompletion chatCompletion, string prompt, OpenAIPromptExecutionSettings executionSettings, int consoleLinesPerResult)
    {
        var messagePerChoice = new Dictionary<int, string>();
        await foreach (var textUpdate in chatCompletion.GetStreamingContentAsync<StreamingChatContent>(prompt, executionSettings))
        {
            string newContent = string.Empty;
            Console.SetCursorPosition(0, textUpdate.ChoiceIndex * consoleLinesPerResult);

            if (textUpdate.ContentUpdate is { Length: > 0 })
            {
                newContent += textUpdate.ContentUpdate;
            }

            if (!messagePerChoice.ContainsKey(textUpdate.ChoiceIndex))
            {
                messagePerChoice.Add(textUpdate.ChoiceIndex, string.Empty);
            }
            messagePerChoice[textUpdate.ChoiceIndex] += newContent;

            Console.Write(messagePerChoice[textUpdate.ChoiceIndex]);
        }
    }
}
