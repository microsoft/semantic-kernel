// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example36_MultiCompletion
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Text Completion - Multi Results  ========");

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
            ResultsPerPrompt = 2,
        };

        var prompt = "Write one paragraph why AI is awesome";

        foreach (ITextCompletionResult completionResult in await textCompletion.CompleteMultiAsync(prompt, requestSettings))
        {
            Console.WriteLine(await completionResult.CompleteAsync());
            Console.WriteLine("-------------");
        }

        Console.WriteLine();
    }
}
