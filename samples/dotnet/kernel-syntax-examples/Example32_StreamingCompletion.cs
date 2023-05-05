// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example32_StreamingCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAITextCompletionStreamAsync();
        await OpenAITextCompletionStreamAsync();
        await CustomTextCompletionStreamAsync();
    }

    private static async Task AzureOpenAITextCompletionStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Streaming TextCompletion ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureTextCompletionService(
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task OpenAITextCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Streaming TextCompletion ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddOpenAITextCompletionService("text-davinci-003", Env.Var("OPENAI_API_KEY"), serviceId: "text-davinci-003");

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task CustomTextCompletionStreamAsync()
    {
        Console.WriteLine("======== Custom - Streaming TextCompletion ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        ITextCompletion Factory(IKernel k) => new MyTextCompletionService();

        // Add your text completion service
        kernel.Config.AddTextCompletionService(Factory);

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task TextCompletionStreamAsync(ITextCompletion textCompletion)
    {
        var requestSettings = new CompleteRequestSettings()
        {
            MaxTokens = 100,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        var prompt = "Write one paragraph why AI is awesome";

        Console.WriteLine("Prompt: " + prompt);
        await foreach (string message in textCompletion.CompleteStreamAsync(prompt, requestSettings))
        {
            Console.Write(message);
        }

        Console.WriteLine();

        /* Output (Fluid content):

        AI is awesome because it can help us solve complex problems, enhance our creativity,
        and improve our lives in many ways. AI can perform tasks that are too difficult, tedious,
        or dangerous for humans, such as diagnosing diseases, detecting fraud, or exploring space.
        AI can also augment our abilities and inspire us to create new forms of art, music, or
        literature. AI can also improve our well-being and happiness by providing personalized
        recommendations, entertainment, and assistance. AI is awesome
       
        */
    }

    private class MyTextCompletionService : ITextCompletion
    {
        private readonly string _outputResult =
            @"AI is awesome because it can help us solve complex problems, enhance our creativity,
and improve our lives in many ways. AI can perform tasks that are too difficult, tedious,
or dangerous for humans, such as diagnosing diseases, detecting fraud, or exploring space.
AI can also augment our abilities and inspire us to create new forms of art, music, or
literature. AI can also improve our well-being and happiness by providing personalized
recommendations, entertainment, and assistance. AI is awesome";

        public Task<string> CompleteAsync(
            string text,
            CompleteRequestSettings requestSettings,
            CancellationToken cancellationToken = default)
        {
            // Your model logic here
            var result = this._outputResult;

            return Task.FromResult(result);
        }

        public async IAsyncEnumerable<string> CompleteStreamAsync(
            string text,
            CompleteRequestSettings requestSettings,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            yield return Environment.NewLine;

            var streamedOutput = this._outputResult.Split(' ');
            foreach (string word in streamedOutput)
            {
                await Task.Delay(50, cancellationToken);
                yield return $"{word} ";
            }
        }
    }
}
