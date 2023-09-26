// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with streaming Multiple Results Chat Completion
 */
// ReSharper disable once InconsistentNaming
public static class Example37_MultiStreamingCompletion
{
    private static readonly object s_lockObject = new();

    public static async Task RunAsync()
    {
        //await AzureOpenAIMultiTextCompletionStreamAsync();
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

        ITextCompletion textCompletion = new OpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task TextCompletionStreamAsync(ITextCompletion textCompletion)
    {
        var requestSettings = new OpenAIRequestSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        var prompt = "Write one paragraph why AI is awesome";
        var consoleLinesPerResult = 12;

        PrepareDisplay();

        List<Task> resultTasks = new();
        int currentResult = 0;
        using var ct = new CancellationTokenSource();
        await foreach (var completionResult in textCompletion.GetStreamingCompletionsAsync(prompt, requestSettings, ct.Token))
        {
            resultTasks.Add(ProcessStreamAsyncEnumerableAsync(completionResult, currentResult++, consoleLinesPerResult));
        }

        Console.WriteLine();

        await Task.WhenAll(resultTasks.ToArray());


        // Streaming result
        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var fixedFunction = kernel.CreateSemanticFunction($"Write a paragraph about streaming",
                requestSettings: new OpenAIRequestSettings
                {
                    Streaming = true,
                    MaxTokens = 1000,
                    ResultsPerPrompt = 2
                });

        var result = await kernel.RunAsync(fixedFunction);
        await foreach (string token in (await kernel.RunAsync(fixedFunction)).GetValue<IAsyncEnumerable<string>>()!)
        {
            Console.Write(token);
        }

        /*
        
        int position = 0;
        await foreach (ITextCompletionStreamingResult completionResult in textCompletion.CompleteMultiStreamAsync(prompt, requestSettings))
        {
            string fullMessage = string.Empty;

            await foreach (string message in completionResult.GetCompletionStreamingAsync())
            {
                fullMessage += message;

                Console.SetCursorPosition(0, (position * consoleLinesPerResult));
                Console.Write(fullMessage);
            }

            position++;
        }*/

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
