// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Text Completion as streaming
 */

// ReSharper disable once InconsistentNaming
// ReSharper disable CommentTypo
public static class Example31_StreamingCompletion
{
    public static async Task RunAsync()
    {
        await AzureTextCompletionSampleAsync();
    }

    private static async Task AzureTextCompletionSampleAsync()
    {
        Console.WriteLine("======== Streaming TextCompletion ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureTextCompletionService(
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        ITextCompletion textCompletion = kernel.GetService<ITextCompletion>();

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

        /* Output (Fluid content):

        AI is awesome because it can help us solve complex problems, enhance our creativity,
        and improve our lives in many ways. AI can perform tasks that are too difficult, tedious,
        or dangerous for humans, such as diagnosing diseases, detecting fraud, or exploring space.
        AI can also augment our abilities and inspire us to create new forms of art, music, or
        literature. AI can also improve our well-being and happiness by providing personalized
        recommendations, entertainment, and assistance. AI is awesome
       
        */
    }
}
