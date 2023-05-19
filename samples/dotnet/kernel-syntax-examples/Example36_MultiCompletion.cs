// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example36_MultiCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiTextCompletionAsync();
        await OpenAITextCompletionAsync();
    }

    private static async Task AzureOpenAIMultiTextCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Text Completion ========");

        IKernel kernel = new KernelBuilder()
            .WithAzureTextCompletionService(
                Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"))
            .WithLogger(ConsoleLogger.Log).Build();

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

        await TextCompletionAsync(textCompletion);
    }

    private static async Task OpenAITextCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion ========");

        IKernel kernel = new KernelBuilder()
            .WithOpenAITextCompletionService("text-davinci-003", Env.Var("OPENAI_API_KEY"), serviceId: "text-davinci-003")
            .WithLogger(ConsoleLogger.Log).Build();

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

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

        foreach (ITextCompletionResult completionResult in await textCompletion.GetCompletionsAsync(prompt, requestSettings))
        {
            Console.WriteLine(await completionResult.GetCompletionAsync());
            Console.WriteLine("-------------");
        }

        Console.WriteLine();
    }
}
