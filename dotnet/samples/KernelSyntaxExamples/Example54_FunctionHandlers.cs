// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

#pragma warning disable RCS1214 // Unnecessary interpolated string.

// ReSharper disable once InconsistentNaming
public static class Example54_FunctionHandlers
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Using Function Execution Handlers ========");

        string openAIModelId = TestConfiguration.OpenAI.ModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId == null || openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
            .WithOpenAITextCompletionService(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        const string FunctionDefinition = "Write a paragraph about: {{$input}}.";

        var excuseFunction = kernel.CreateSemanticFunction(FunctionDefinition, maxTokens: 100, temperature: 0.4, topP: 1);

        Task MyPreHandler(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Execution Handler - Prompt: {executionContext.Prompt}");

            return Task.CompletedTask;
        }

        Task MyCancelledPreExecutionHandler(PreExecutionContext executionContext)
        {
            Console.WriteLine("Pre Execution Handler - Should not trigger");

            return Task.CompletedTask;
        }

        Task MyPreHandler2(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Execution Handler 2 - Prompt Token: {GPT3Tokenizer.Encode(executionContext.Prompt!).Count}");

            return Task.CompletedTask;
        }

        Task MyPostExecutionHandler(PostExecutionContext executionContext)
        {
            Console.WriteLine($"Post Execution Handler - Total Tokens: {executionContext.SKContext.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
            return Task.CompletedTask;
        }

        excuseFunction.SetPreExecutionHandler(MyPreHandler);
        excuseFunction.SetPreExecutionHandler(MyPreHandler2);
        var HandlerToCancel = excuseFunction.SetPreExecutionHandler(MyCancelledPreExecutionHandler);

        excuseFunction.SetPostExecutionHandler(MyPostExecutionHandler);

        HandlerToCancel.Cancel();

        var result = await excuseFunction.InvokeAsync("I missed the F1 final race");

        Console.WriteLine($"Function Result: {result}");
    }
}
