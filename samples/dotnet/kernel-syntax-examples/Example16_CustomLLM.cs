// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public async Task<string> CompleteAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        await Task.Delay(0, cancellationToken);

        // Your model logic here
        var result = "...output from your custom model...";

        return result;
    }
}

// ReSharper disable StringLiteralTypo
// ReSharper disable once InconsistentNaming
public static class Example16_CustomLLM
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Custom LLM / Text Completion AI ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        ITextCompletion Factory(IKernel k) => new MyTextCompletionService();

        // Add your text completion service
        kernel.Config.AddTextCompletionService("myService", Factory);

        const string FUNCTION_DEFINITION = "Does the text contain grammar errors (Y/N)? Text: {{$input}}";

        var textValidationFunction = kernel.CreateSemanticFunction(FUNCTION_DEFINITION);

        var result = await textValidationFunction.InvokeAsync("I mised the training sesion this morning");
        Console.WriteLine(result);
    }
}
