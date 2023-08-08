// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example53_FunctionHooks
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Using Function Hooks ========");

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

        Task MyPreHook(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Hook - Prompt: {executionContext.Prompt}");

            return Task.CompletedTask;
        }

        Task MyCancelledPreHook(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Hook - Should not trigger");

            return Task.CompletedTask;
        }

        Task MyPreHook2(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Hook 2 - Prompt Token: {GPT3Tokenizer.Encode(executionContext.Prompt!).Count}");

            return Task.CompletedTask;
        }

        Task MyPostHook(PostExecutionContext executionContext)
        {
            Console.WriteLine($"Post Hook - Total Tokens: {executionContext.SKContext.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
            return Task.CompletedTask;
        }

        excuseFunction.SetPreExecutionHook(MyPreHook);
        excuseFunction.SetPreExecutionHook(MyPreHook2);
        var hookToCancel = excuseFunction.SetPreExecutionHook(MyCancelledPreHook);

        excuseFunction.SetPostExecutionHook(MyPostHook);

        hookToCancel.Cancel();

        var result = await excuseFunction.InvokeAsync("I missed the F1 final race");

        Console.WriteLine($"Function Result: {result}");
    }
}
