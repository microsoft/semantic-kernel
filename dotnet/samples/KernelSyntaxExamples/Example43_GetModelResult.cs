// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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

        // Using the Kernel InvokeAsync
        var result = await kernel.InvokeAsync(myFunction, "sorry I forgot your birthday");
        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson());
        Console.WriteLine();

        // Using Chat Completion directly
        var chatCompletionService = new OpenAIChatCompletionService(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        var prompt = FunctionDefinition.Replace("{{$input}}", $"Translate this date {DateTimeOffset.Now:f} to French format", StringComparison.InvariantCultureIgnoreCase);

        var textContent = await chatCompletionService.GetTextContentAsync(prompt, new OpenAIPromptExecutionSettings() { MaxTokens = 500, Temperature = 1, TopP = 0.5 }, kernel);

        Console.WriteLine(textContent);
        Console.WriteLine(textContent.Metadata?["Usage"]?.AsJson());
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
