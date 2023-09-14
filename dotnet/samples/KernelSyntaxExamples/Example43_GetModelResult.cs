// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using RepoUtils;

#pragma warning disable RCS1192 // (Unnecessary usage of verbatim string literal)

// ReSharper disable once InconsistentNaming
public static class Example43_GetModelResult
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Result ========");

        IKernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletionService(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Function defined using few-shot design pattern
        const string FunctionDefinition = "Hi, give me 5 book suggestions about: {{$input}}";

        var myFunction = kernel.CreateSemanticFunction(FunctionDefinition);

        // Using InvokeAsync with 3 results (Currently invoke only supports 1 result, but you can get the other results from the ModelResults)
        var textResult = await myFunction.InvokeAsync("Sci-fi",
            requestSettings: new OpenAIRequestSettings { ResultsPerPrompt = 3, MaxTokens = 500, Temperature = 1, TopP = 0.5 });
        Console.WriteLine(textResult);
        Console.WriteLine(textResult.ModelResults.Select(result => result.GetOpenAIChatResult()).AsJson());
        Console.WriteLine();

        // Using the Kernel RunAsync
        textResult = await kernel.RunAsync("sorry I forgot your birthday", myFunction);
        Console.WriteLine(textResult);
        Console.WriteLine(textResult.ModelResults.LastOrDefault()?.GetOpenAIChatResult()?.Usage.AsJson());
        Console.WriteLine();

        // Using Chat Completion directly
        var chatCompletion = new OpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        var prompt = FunctionDefinition.Replace("{{$input}}", $"Translate this date {DateTimeOffset.Now:f} to French format", StringComparison.InvariantCultureIgnoreCase);

        IReadOnlyList<ITextResult> completionResults = await chatCompletion.GetCompletionsAsync(prompt, new OpenAIRequestSettings() { MaxTokens = 500, Temperature = 1, TopP = 0.5 });

        Console.WriteLine(await completionResults[0].GetCompletionAsync());
        Console.WriteLine(completionResults[0].ModelResult.GetOpenAIChatResult().Usage.AsJson());
        Console.WriteLine();

        // Getting the error details
        kernel = new KernelBuilder()
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "Invalid Key")
            .Build();
        var errorFunction = kernel.CreateSemanticFunction(FunctionDefinition);

#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            await kernel.RunAsync("sorry I forgot your birthday", errorFunction);
        }
        catch (Exception ex)
        {
            Console.WriteLine(OutputExceptionDetail(ex.InnerException));
        }
#pragma warning restore CA1031 // Do not catch general exception types

        string OutputExceptionDetail(Exception? exception)
        {
            return exception switch
            {
                HttpOperationException httpException => new { StatusCode = httpException.StatusCode?.ToString(), Message = httpException.Message, Response = httpException.ResponseContent }.AsJson(),
                { } e => new { e.Message }.AsJson(),
                _ => string.Empty
            };
        }
    }
}
