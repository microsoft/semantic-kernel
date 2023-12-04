// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextGeneration;

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
        await AzureOpenAITextGenerationStreamAsync();
        await OpenAITextGenerationStreamAsync();
    }

    private static async Task AzureOpenAITextGenerationStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Text Completion - Raw Streaming ========");

        var textCompletion = new AzureOpenAITextGeneration(
            TestConfiguration.AzureOpenAI.DeploymentName,
            TestConfiguration.AzureOpenAI.ModelId,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await TextGenerationStreamAsync(textCompletion);
    }

    private static async Task OpenAITextGenerationStreamAsync()
    {
        Console.WriteLine("======== Open AI - Text Completion - Raw Streaming ========");

        var textCompletion = new OpenAITextGeneration("text-davinci-003", TestConfiguration.OpenAI.ApiKey);

        await TextGenerationStreamAsync(textCompletion);
    }

    private static async Task TextGenerationStreamAsync(ITextGeneration textCompletion)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 100,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        var prompt = "Write one paragraph why AI is awesome";

        Console.WriteLine("Prompt: " + prompt);
        await foreach (string message in textCompletion.GetStreamingContentAsync<string>(prompt, executionSettings))
        {
            Console.Write(message);
        }

        Console.WriteLine();
    }
}
