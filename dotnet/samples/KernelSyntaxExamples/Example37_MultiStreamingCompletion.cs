// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

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

        var chatCompletionService = new AzureOpenAIChatCompletionService(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.ChatModelId,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await ChatCompletionStreamAsync(chatCompletionService);
    }

    private static async Task OpenAIChatCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion - Raw Streaming ========");

        ITextGenerationService textGeneration = new OpenAIChatCompletionService(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        await ChatCompletionStreamAsync(textGeneration);
    }

    private static async Task ChatCompletionStreamAsync(ITextGenerationService textGeneration)
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
        await ProcessStreamAsyncEnumerableAsync(textGeneration, prompt, executionSettings, consoleLinesPerResult);

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
    private static async Task ProcessStreamAsyncEnumerableAsync(ITextGenerationService chatCompletion, string prompt, OpenAIPromptExecutionSettings executionSettings, int consoleLinesPerResult)
    {
        var messagePerChoice = new Dictionary<int, string>();
        await foreach (var textUpdate in chatCompletion.GetStreamingTextContentsAsync(prompt, executionSettings))
        {
            string newContent = string.Empty;
            Console.SetCursorPosition(0, textUpdate.ChoiceIndex * consoleLinesPerResult);

            if (textUpdate.Text is { Length: > 0 })
            {
                newContent += textUpdate.Text;
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
