// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using RepoUtils;

#pragma warning disable RCS1192 // (Unnecessary usage of verbatim string literal)

// ReSharper disable once InconsistentNaming
public static class Example43_GetModelResult
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Result ========");

        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Function defined using few-shot design pattern
        const string FunctionDefinition = "Hi, give me 5 book suggestions about: {{$input}}";

        var myFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        // Using InvokeAsync with 3 results (Currently invoke only supports 1 result, but you can get the other results from the ModelResults)
        var functionResult = await myFunction.InvokeAsync(kernel, new KernelArguments(new OpenAIPromptExecutionSettings { ResultsPerPrompt = 3, MaxTokens = 500, Temperature = 1, TopP = 0.5 })
        {
            [KernelArguments.InputParameterName] = "Sci-fi"
        });

        Console.WriteLine(functionResult.GetValue<string>());
        Console.WriteLine(functionResult.GetModelResults()?.Select(result => result.GetOpenAIChatResult()).AsJson());
        Console.WriteLine();

        // Using the Kernel InvokeAsync
        var result = await kernel.InvokeAsync(myFunction, "sorry I forgot your birthday");
        var modelResults = result.GetModelResults() ?? Enumerable.Empty<ModelResult>();

        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine(modelResults.LastOrDefault()?.GetOpenAIChatResult()?.Usage.AsJson());
        Console.WriteLine();

        // Using Chat Completion directly
        var chatCompletion = new OpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        var prompt = FunctionDefinition.Replace("{{$input}}", $"Translate this date {DateTimeOffset.Now:f} to French format", StringComparison.InvariantCultureIgnoreCase);

        IReadOnlyList<ITextResult> completionResults = await chatCompletion.GetCompletionsAsync(prompt, new OpenAIPromptExecutionSettings() { MaxTokens = 500, Temperature = 1, TopP = 0.5 }, kernel);

        Console.WriteLine(await completionResults[0].GetCompletionAsync());
        Console.WriteLine(completionResults[0].ModelResult.GetOpenAIChatResult().Usage.AsJson());
        Console.WriteLine();

        // Getting the error details
        kernel = new KernelBuilder()
            .WithOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, "Invalid Key")
            .Build();
        var errorFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            await kernel.InvokeAsync(errorFunction, "sorry I forgot your birthday");
        }
        catch (Exception ex)
        {
            Console.WriteLine(OutputExceptionDetail(ex));
        }
#pragma warning restore CA1031 // Do not catch general exception types

        static string OutputExceptionDetail(Exception? exception)
        {
            return exception switch
            {
                HttpOperationException httpException => new { StatusCode = httpException.StatusCode?.ToString(), Message = httpException.Message, Response = httpException.ResponseContent }.AsJson(),
                { } e => e.Message,
                _ => string.Empty
            };
        }
    }
}
