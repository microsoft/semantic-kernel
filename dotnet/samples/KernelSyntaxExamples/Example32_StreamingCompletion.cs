// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/**
 * The following example shows how to use Semantic Kernel with streaming Text Completion.
 *
 * Note that all text completion models are deprecated by OpenAI and will be removed in a future release.
 *
 * Refer to example 33 for streaming chat completion.
 */
// ReSharper disable once InconsistentNaming
public static class Example32_StreamingCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIKernelStreamAsync();
        await OpenAIKernelStreamAsync();

        await AzureOpenAITextCompletionStreamAsync();
        await OpenAITextCompletionStreamAsync();
    }

    private async static Task AzureOpenAIKernelStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Kernel RunAsync - Text Streaming ========");

        var kernel = Kernel.Builder.WithAzureTextCompletionService(
            TestConfiguration.AzureOpenAI.DeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        var prompt = "Write one paragraph why AI is awesome";
        var function = kernel.CreateSemanticFunction(prompt, requestSettings: new() { Streaming = true });
        var result = await kernel.RunAsync(function);

        Console.WriteLine("Prompt: " + prompt);
        await foreach (string message in result.GetValue<IAsyncEnumerable<string>>()!)
        {
            Console.Write(message);
        }
        Console.WriteLine();
    }

    private async static Task OpenAIKernelStreamAsync()
    {
        Console.WriteLine("======== OpenAI - Kernel RunAsync - Text Streaming ========");

        var kernel = Kernel.Builder.WithOpenAITextCompletionService(
            TestConfiguration.OpenAI.ModelId,
            TestConfiguration.OpenAI.ApiKey)
            .Build();

        var prompt = "Write one paragraph why AI is awesome";
        var function = kernel.CreateSemanticFunction(prompt, requestSettings: new() { Streaming = true });
        var result = await kernel.RunAsync(function);

        Console.WriteLine("Prompt: " + prompt);
        await foreach (string message in result.GetValue<IAsyncEnumerable<string>>()!)
        {
            Console.Write(message);
        }
        Console.WriteLine();
    }

    private static async Task AzureOpenAITextCompletionStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Text Completion - Raw Streaming ========");

        var textCompletion = new AzureTextCompletion(
            TestConfiguration.AzureOpenAI.DeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task OpenAITextCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Text Completion - Raw Streaming ========");

        var textCompletion = new OpenAITextCompletion("text-davinci-003", TestConfiguration.OpenAI.ApiKey);

        await TextCompletionStreamAsync(textCompletion);
    }

    private static async Task TextCompletionStreamAsync(ITextCompletion textCompletion)
    {
        var requestSettings = new OpenAIRequestSettings()
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
    }
}
