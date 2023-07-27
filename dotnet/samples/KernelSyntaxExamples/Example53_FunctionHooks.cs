// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
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

        SKContext MyPreHook(SKContext context, string generatedPrompt)
        {
            Console.WriteLine($"Pre Hook - Prompt: {generatedPrompt}");
            return context;
        }

        SKContext MyPostHook(SKContext context)
        {
            Console.WriteLine($"Post Hook - Total Tokens: {context.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
            return context;
        }

        excuseFunction.SetPreExecutionHook(MyPreHook);
        excuseFunction.SetPostExecutionHook(MyPostHook);

        var result = await excuseFunction.InvokeAsync("I missed the F1 final race");

        Console.WriteLine($"Function Result: {result}");
    }
}
