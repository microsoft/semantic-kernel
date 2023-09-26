// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
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
    private static readonly object s_lockObject = new();

    public static async Task RunAsync()
    {
        await AzureOpenAIMultiTextCompletionStreamAsync();
        await OpenAITextCompletionStreamAsync();
    }

    private static async Task AzureOpenAIMultiTextCompletionStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Text Completion - Raw Streaming ========");

        var textCompletion = new AzureChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task OpenAITextCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion - Raw Streaming ========");

        ITextStreamingCompletion textCompletion = new OpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task TextCompletionStreamAsync(ITextStreamingCompletion textCompletion)
    {
        var requestSettings = new OpenAIRequestSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 3
        };

        var prompt = "Write one paragraph why AI is awesome";
        var consoleLinesPerResult = 12;

        PrepareDisplay();

        List<Task> resultTasks = new();
        int currentResult = 0;
        await foreach (var completionResult in textCompletion.GetStreamingCompletionsAsync(prompt, requestSettings, CancellationToken.None))
        {
            resultTasks.Add(ProcessStreamAsyncEnumerableAsync(completionResult, currentResult++, consoleLinesPerResult));
        }

        Console.WriteLine();

        await Task.WhenAll(resultTasks.ToArray());

        Console.SetCursorPosition(0, requestSettings.ResultsPerPrompt * consoleLinesPerResult);
        Console.WriteLine();
    }

    private static async Task ProcessStreamAsyncEnumerableAsync(ITextStreamingResult result, int resultNumber, int linesPerResult)
    {
        var fullSentence = string.Empty;
        await foreach (var word in result.GetCompletionStreamingAsync())
        {
            fullSentence += word;

            lock (s_lockObject)
            {
                Console.SetCursorPosition(0, (resultNumber * linesPerResult));
                Console.Write(fullSentence);
            }
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
}
