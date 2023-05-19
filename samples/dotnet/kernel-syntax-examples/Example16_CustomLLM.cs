// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to plug into SK a custom text completion model.
 *
 * This might be useful in a few scenarios, for example:
 * - You are not using OpenAI or Azure OpenAI models
 * - You are using OpenAI/Azure OpenAI models but the models are behind a web service with a different API schema
 * - You want to use a local model
 */
public class MyTextCompletionService : ITextCompletion
{
    public Task<IReadOnlyList<ITextCompletionResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<IReadOnlyList<ITextCompletionResult>>(new List<ITextCompletionResult>
        {
            new MyTextCompletionStreamingResult()
        });
    }

    public IAsyncEnumerable<ITextCompletionStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        return new List<ITextCompletionStreamingResult>()
        {
            new MyTextCompletionStreamingResult()
        }.ToAsyncEnumerable();
    }
}

public class MyTextCompletionStreamingResult : ITextCompletionStreamingResult
{
    private const string Text = @" ..output from your custom model... Example:
AI is awesome because it can help us solve complex problems, enhance our creativity,
and improve our lives in many ways. AI can perform tasks that are too difficult,
tedious, or dangerous for humans, such as diagnosing diseases, detecting fraud, or
exploring space. AI can also augment our abilities and inspire us to create new forms
of art, music, or literature. AI can also improve our well-being and happiness by
providing personalized recommendations, entertainment, and assistance. AI is awesome";

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        // Forcing a 2 sec delay (Simulating custom LLM lag)
        await Task.Delay(2000, cancellationToken);

        return Text;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        yield return Environment.NewLine;

        // Your model logic here
        var streamedOutput = Text.Split(' ');
        foreach (string word in streamedOutput)
        {
            await Task.Delay(50, cancellationToken);
            yield return $"{word} ";
        }
    }
}

// ReSharper disable StringLiteralTypo
// ReSharper disable once InconsistentNaming
public static class Example16_CustomLLM
{
    public static async Task RunAsync()
    {
        await CustomTextCompletionWithSKFunctionAsync();

        await CustomTextCompletionAsync();
        await CustomTextCompletionStreamAsync();
    }

    private static async Task CustomTextCompletionWithSKFunctionAsync()
    {
        Console.WriteLine("======== Custom LLM - Text Completion - SKFunction ========");

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            // Add your text completion service as a singleton instance
            .WithAIService<ITextCompletion>("myService1", new MyTextCompletionService())
            // Add your text completion service as a factory method
            .WithAIService<ITextCompletion>("myService2", (_) => new MyTextCompletionService())
            .Build();

        const string FunctionDefinition = "Does the text contain grammar errors (Y/N)? Text: {{$input}}";

        var textValidationFunction = kernel.CreateSemanticFunction(FunctionDefinition);

        var result = await textValidationFunction.InvokeAsync("I mised the training sesion this morning");
        Console.WriteLine(result);
    }

    private static async Task CustomTextCompletionAsync()
    {
        Console.WriteLine("======== Custom LLM  - Text Completion - Raw ========");
        var completionService = new MyTextCompletionService();

        var result = await completionService.CompleteAsync("I missed the training sesion this morning", new CompleteRequestSettings());

        Console.WriteLine(result);
    }

    private static async Task CustomTextCompletionStreamAsync()
    {
        Console.WriteLine("======== Custom LLM  - Text Completion - Raw Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        ITextCompletion textCompletion = new MyTextCompletionService();

        var prompt = "Write one paragraph why AI is awesome";
        await TextCompletionStreamAsync(prompt, textCompletion);
    }

    private static async Task TextCompletionStreamAsync(string prompt, ITextCompletion textCompletion)
    {
        var requestSettings = new CompleteRequestSettings()
        {
            MaxTokens = 100,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        Console.WriteLine("Prompt: " + prompt);
        await foreach (string message in textCompletion.CompleteStreamAsync(prompt, requestSettings))
        {
            Console.Write(message);
        }

        Console.WriteLine();
    }
}
