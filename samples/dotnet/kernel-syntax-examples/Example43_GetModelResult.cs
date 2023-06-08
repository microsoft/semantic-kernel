// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example43_GetModelResult
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Result ========");

        IKernel kernel = new KernelBuilder()
            .WithOpenAITextCompletionService("text-davinci-003", Env.Var("OPENAI_API_KEY"))
            .Build();

        // Function defined using few-shot design pattern
        const string FunctionDefinition = @"
Generate a creative reason or excuse for the given event.
Be creative and be funny. Let your imagination run wild.

Event: I am running late.
Excuse: I was being held ransom by giraffe gangsters.

Event: I haven't been to the gym for a year
Excuse: I've been too busy training my pet dragon.

Event: {{$input}}
";

        var excuseFunction = kernel.CreateSemanticFunction(FunctionDefinition, maxTokens: 100, temperature: 0.4, topP: 1);

        // Using InvokeAsync
        var textResult = await excuseFunction.InvokeAsync("I missed the F1 final race");
        Console.WriteLine(textResult);
        Console.WriteLine(textResult.ModelResults.Select(result => result.GetOpenAITextResult()).AsJson());
        Console.WriteLine();

        // Using the Kernel RunAsync
        textResult = await kernel.RunAsync("sorry I forgot your birthday", excuseFunction);
        Console.WriteLine(textResult);
        Console.WriteLine(textResult.ModelResults.LastOrDefault()?.GetOpenAITextResult()?.Usage.AsJson());
        Console.WriteLine();

        // Using Chat Completion directly
        var chatCompletion = new OpenAIChatCompletion("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"));
        var prompt = FunctionDefinition.Replace("{{$input}}", $"Translate this date {DateTimeOffset.Now:f} to French format", StringComparison.InvariantCultureIgnoreCase);

        IReadOnlyList<ITextCompletionResult> completionResults = await chatCompletion.GetCompletionsAsync(prompt, new CompleteRequestSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });
        Console.WriteLine(await completionResults[0].GetCompletionAsync());
        Console.WriteLine(completionResults[0].ModelResult.GetOpenAIChatResult().Usage.AsJson());
        Console.WriteLine();

        // Getting the error details
        kernel = new KernelBuilder()
            .WithOpenAITextCompletionService("text-davinci-003", "Invalid Key")
            .Build();
        var errorFunction = kernel.CreateSemanticFunction(FunctionDefinition);
        var failedContext = await kernel.RunAsync("sorry I forgot your birthday", errorFunction);

        if (failedContext.ErrorOccurred)
        {
            Console.WriteLine(OutputExceptionDetail(failedContext.LastException?.InnerException));
        }

        string OutputExceptionDetail(Exception? exception)
        {
            return exception switch
            {
                RequestFailedException requestException => new { requestException.Status, requestException.Message }.AsJson(),
                AIException aiException => new { ErrorCode = aiException.ErrorCode.ToString(), aiException.Message, aiException.Detail }.AsJson(),
                { } e => new { e.Message }.AsJson(),
                _ => string.Empty
            };
        }
    }
}
