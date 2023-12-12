// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;

/**
 * The following example shows how to plug a custom text generation model into SK.
 *
 * To do this, this example uses a text generation service stub (MyTextGenerationService) and
 * no actual model.
 *
 * Using a custom text generation model within SK can be useful in a few scenarios, for example:
 * - You are not using OpenAI or Azure OpenAI models
 * - You are using OpenAI/Azure OpenAI models but the models are behind a web service with a different API schema
 * - You want to use a local model
 *
 * Note that all OpenAI text generation models are deprecated and no longer available to new customers.
 *
 * Refer to example 33 for streaming chat completion.
 */
// ReSharper disable once InconsistentNaming
public static class Example16_CustomLLM
{
    public static async Task RunAsync()
    {
        await CustomTextGenerationWithSKFunctionAsync();
        await CustomTextGenerationAsync();
        await CustomTextGenerationStreamAsync();
    }

    private static async Task CustomTextGenerationWithSKFunctionAsync()
    {
        Console.WriteLine("\n======== Custom LLM - Text Completion - SKFunction ========");

        IKernelBuilder builder = Kernel.CreateBuilder();
        // Add your text generation service as a singleton instance
        builder.Services.AddKeyedSingleton<ITextGenerationService>("myService1", new MyTextGenerationService());
        // Add your text generation service as a factory method
        builder.Services.AddKeyedSingleton<ITextGenerationService>("myService2", (_, _) => new MyTextGenerationService());
        Kernel kernel = builder.Build();

        const string FunctionDefinition = "Write one paragraph on {{$input}}";
        var paragraphWritingFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        const string Input = "Why AI is awesome";
        Console.WriteLine($"Function input: {Input}\n");
        var result = await paragraphWritingFunction.InvokeAsync(kernel, new() { ["input"] = Input });

        Console.WriteLine(result);
    }

    private static async Task CustomTextGenerationAsync()
    {
        Console.WriteLine("\n======== Custom LLM  - Text Completion - Raw ========");

        const string Prompt = "Write one paragraph on why AI is awesome.";
        var completionService = new MyTextGenerationService();

        Console.WriteLine($"Prompt: {Prompt}\n");
        var result = await completionService.GetTextContentAsync(Prompt);

        Console.WriteLine(result);
    }

    private static async Task CustomTextGenerationStreamAsync()
    {
        Console.WriteLine("\n======== Custom LLM  - Text Completion - Raw Streaming ========");

        const string Prompt = "Write one paragraph on why AI is awesome.";
        var completionService = new MyTextGenerationService();

        Console.WriteLine($"Prompt: {Prompt}\n");
        await foreach (var message in completionService.GetStreamingTextContentsAsync(Prompt))
        {
            Console.Write(message);
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Text generation service stub.
    /// </summary>
    private sealed class MyTextGenerationService : ITextGenerationService
    {
        private const string LLMResultText = @"...output from your custom model... Example:
AI is awesome because it can help us solve complex problems, enhance our creativity,
and improve our lives in many ways. AI can perform tasks that are too difficult,
tedious, or dangerous for humans, such as diagnosing diseases, detecting fraud, or
exploring space. AI can also augment our abilities and inspire us to create new forms
of art, music, or literature. AI can also improve our well-being and happiness by
providing personalized recommendations, entertainment, and assistance. AI is awesome.";

        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

        public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            foreach (string word in LLMResultText.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            {
                await Task.Delay(50, cancellationToken);
                cancellationToken.ThrowIfCancellationRequested();

                yield return new StreamingTextContent($"{word} ");
            }
        }

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<TextContent>>(new List<TextContent>
            {
                new(LLMResultText)
            });
        }
    }
}
