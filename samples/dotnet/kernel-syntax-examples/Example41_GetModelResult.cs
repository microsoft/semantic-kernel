// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example41_GetModelResult
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Result ========");

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
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
        Console.WriteLine(JsonSerializer.Serialize(
            textResult.GetOpenAILastPromptResult(),
            new JsonSerializerOptions() { WriteIndented = true }
        ));
        Console.WriteLine();

        // Using the Kernel RunAsync
        textResult = await kernel.RunAsync("sorry I forgot your birthday", excuseFunction);
        Console.WriteLine(textResult);
        Console.WriteLine(JsonSerializer.Serialize(
            textResult.GetOpenAILastPromptResult()?.Usage,
            new JsonSerializerOptions() { WriteIndented = true }
        ));
        Console.WriteLine();

        // Using the Text Completion directly
        var textCompletion = kernel.GetService<ITextCompletion>();
        var prompt = FunctionDefinition.Replace($"{{$input}}", $"Translate this date {DateTimeOffset.Now:f} to French format", StringComparison.InvariantCultureIgnoreCase);

        IReadOnlyList<ITextCompletionResult> completionResults = await textCompletion.GetCompletionsAsync(prompt, new CompleteRequestSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });
        Console.WriteLine(await completionResults[0].GetCompletionAsync());
        Console.WriteLine(JsonSerializer.Serialize(
            completionResults[0].GetOpenAILastResultData()?.Usage,
            new JsonSerializerOptions() { WriteIndented = true }
        ));
        Console.WriteLine();
    }
}
