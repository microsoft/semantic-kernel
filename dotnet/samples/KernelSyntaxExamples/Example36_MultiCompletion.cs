// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example36_MultiCompletion
{
    public static async Task RunAsync(IConfigurationRoot config)
    {
        await AzureOpenAIMultiTextCompletionAsync();
        await OpenAIMultiTextCompletionAsync();
    }

    private static async Task AzureOpenAIMultiTextCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Text Completion ========");

        var textCompletion = new AzureTextCompletion(
            config.GetValue<string>("AzureOpenAI__DeploymentName"),
            config.GetValue<string>("AzureOpenAI__Endpoint"),
            config.GetValue<string>("AzureOpenAI__ApiKey"));

        await TextCompletionAsync(textCompletion);
    }

    private static async Task OpenAIMultiTextCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion ========");

        ITextCompletion textCompletion = new OpenAITextCompletion(
            "text-davinci-003",
            config.GetValue<string>("OpenAI__ApiKey"));

        await TextCompletionAsync(textCompletion);
    }

    private static async Task TextCompletionAsync(ITextCompletion textCompletion)
    {
        var requestSettings = new CompleteRequestSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 2,
        };

        var prompt = "Write one paragraph why AI is awesome";

        foreach (ITextResult completionResult in await textCompletion.GetCompletionsAsync(prompt, requestSettings))
        {
            Console.WriteLine(await completionResult.GetCompletionAsync());
            Console.WriteLine("-------------");
        }

        Console.WriteLine();
    }
}
