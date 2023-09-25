// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example05_InlineFunctionDefinition
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Inline Function Definition ========");

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId == null || openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        /*
         * Example: normally you would place prompt templates in a folder to separate
         *          C# code from natural language code, but you can also define a semantic
         *          function inline if you like.
         */

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
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

        var excuseFunction = kernel.CreateSemanticFunction(FunctionDefinition, requestSettings: new OpenAIRequestSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var result = await kernel.RunAsync("I missed the F1 final race", excuseFunction);
        Console.WriteLine(result.GetValue<string>());

        result = await kernel.RunAsync("sorry I forgot your birthday", excuseFunction);
        Console.WriteLine(result.GetValue<string>());

        var fixedFunction = kernel.CreateSemanticFunction($"Translate this date {DateTimeOffset.Now:f} to French format", requestSettings: new OpenAIRequestSettings() { MaxTokens = 100 });

        result = await kernel.RunAsync(fixedFunction);
        Console.WriteLine(result.GetValue<string>());

        // Streaming result
        fixedFunction = kernel.CreateSemanticFunction($"Translate this date {DateTimeOffset.Now:f} to French format",
                requestSettings: new OpenAIRequestSettings
                {
                    Streaming = true,
                    MaxTokens = 100
                });

        await foreach(string token in (await kernel.RunAsync(fixedFunction)).GetValue<IAsyncEnumerable<string>>()!)
        {
            Console.Write(token);
        }

        Console.WriteLine();
    }
}
