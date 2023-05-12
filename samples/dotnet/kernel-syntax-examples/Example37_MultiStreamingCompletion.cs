// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example37_MultiStreamingCompletion
{
    private static readonly object s_lockObject = new();

    public static async Task RunAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Text Completion - Multi Results Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureTextCompletionService(
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        var textCompletion = (AzureTextCompletion)kernel.GetService<ITextCompletion>();

        var requestSettings = new CompleteRequestSettings()
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
        await foreach (var completionResult in textCompletion.CompleteMultiStreamAsync(prompt, requestSettings))
        {
            resultTasks.Add(ProcessStreamAsyncEnumerableAsync(completionResult, currentResult++, consoleLinesPerResult));
        }

        Console.WriteLine();

        await Task.WhenAll(resultTasks.ToArray());

        /*
        
        int position = 0;
        await foreach (ITextCompletionStreamingResult completionResult in textCompletion.CompleteMultiStreamAsync(prompt, requestSettings))
        {
            string fullMessage = string.Empty;

            await foreach (string message in completionResult.CompleteStreamAsync())
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

    private static async Task ProcessStreamAsyncEnumerableAsync(ITextCompletionStreamingResult result, int resultNumber, int linesPerResult)
    {
        var fullSentence = string.Empty;
        await foreach (var word in result.CompleteStreamAsync())
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
    /// Break enought lines as the current console window size to display the results
    /// </summary>
    private static void PrepareDisplay()
    {
        for (int i = 0; i < Console.WindowHeight - 5; i++)
        {
            Console.WriteLine();
        }
    }
}
