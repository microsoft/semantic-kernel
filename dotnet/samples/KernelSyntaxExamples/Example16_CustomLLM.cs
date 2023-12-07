// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using RepoUtils;

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously

/**
 * The following example shows how to plug into SK a custom text generation model.
 *
 * This might be useful in a few scenarios, for example:
 * - You are not using OpenAI or Azure OpenAI models
 * - You are using OpenAI/Azure OpenAI models but the models are behind a web service with a different API schema
 * - You want to use a local model
 *
 * Note that all text generation models are deprecated by OpenAI and will be removed in a future release.
 *
 * Refer to example 33 for streaming chat completion.
 */
// ReSharper disable StringLiteralTypo
// ReSharper disable once InconsistentNaming
public static class Example16_CustomLLM
{
    private const string LLMResultText = @" ..output from your custom model... Example:
    AI is awesome because it can help us solve complex problems, enhance our creativity,
    and improve our lives in many ways. AI can perform tasks that are too difficult,
    tedious, or dangerous for humans, such as diagnosing diseases, detecting fraud, or
    exploring space. AI can also augment our abilities and inspire us to create new forms
    of art, music, or literature. AI can also improve our well-being and happiness by
    providing personalized recommendations, entertainment, and assistance. AI is awesome";

    public static async Task RunAsync()
    {
        await CustomTextGenerationWithSKFunctionAsync();

        await CustomTextGenerationAsync();
        await CustomTextGenerationStreamAsync();
    }

    private static async Task CustomTextGenerationWithSKFunctionAsync()
    {
        Console.WriteLine("======== Custom LLM - Text Completion - SKFunction ========");

        KernelBuilder builder = new();
        builder.Services.AddSingleton(ConsoleLogger.LoggerFactory);
        // Add your text generation service as a singleton instance
        builder.Services.AddKeyedSingleton<ITextGenerationService>("myService1", new MyTextGenerationService());
        // Add your text generation service as a factory method
        builder.Services.AddKeyedSingleton<ITextGenerationService>("myService2", (_, _) => new MyTextGenerationService());
        Kernel kernel = builder.Build();

        const string FunctionDefinition = "Does the text contain grammar errors (Y/N)? Text: {{$input}}";

        var textValidationFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        var result = await textValidationFunction.InvokeAsync(kernel, new("I mised the training session this morning"));
        Console.WriteLine(result.GetValue<string>());

        // Details of the my custom model response
        Console.WriteLine(JsonSerializer.Serialize(
            result.Metadata,
            new JsonSerializerOptions() { WriteIndented = true }
        ));
    }

    private static async Task CustomTextGenerationAsync()
    {
        Console.WriteLine("======== Custom LLM  - Text Completion - Raw ========");
        var completionService = new MyTextGenerationService();

        var result = await completionService.GetTextContentAsync("I missed the training session this morning");

        Console.WriteLine(result);
    }

    private static async Task CustomTextGenerationStreamAsync()
    {
        Console.WriteLine("======== Custom LLM  - Text Completion - Raw Streaming ========");

        Kernel kernel = new();
        ITextGenerationService textGeneration = new MyTextGenerationService();

        var prompt = "Write one paragraph why AI is awesome";
        await TextGenerationStreamAsync(prompt, textGeneration);
    }

    private static async Task TextGenerationStreamAsync(string prompt, ITextGenerationService textGeneration)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 100,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        Console.WriteLine("Prompt: " + prompt);
        await foreach (var message in textGeneration.GetStreamingTextContentsAsync(prompt, executionSettings))
        {
            Console.Write(message);
        }

        Console.WriteLine();
    }

    private sealed class MyTextGenerationService : ITextGenerationService
    {
        public string? ModelId { get; private set; }

        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

        public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            foreach (string word in LLMResultText.Split(' '))
            {
                await Task.Delay(50, cancellationToken);
                cancellationToken.ThrowIfCancellationRequested();
                yield return new MyStreamingContent($"{word} ");
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

    private sealed class MyStreamingContent : StreamingTextContent
    {
        public MyStreamingContent(string content) : base(content)
        {
        }

        public override byte[] ToByteArray()
        {
            return Encoding.UTF8.GetBytes(this.Text ?? string.Empty);
        }

        public override string ToString()
        {
            return this.Text ?? string.Empty;
        }
    }
}
