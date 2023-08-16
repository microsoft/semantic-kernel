// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.Events;
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
        const string input = "I missed the F1 final race";

        var excuseFunction = kernel.CreateSemanticFunction(FunctionDefinition, maxTokens: 100, temperature: 0.4, topP: 1);

        void MyPreHandler(object? sender, KernelRunningEventArgs e)
        {
            Console.WriteLine($"Pre Execution Handler - Prompt: {e.Prompt}");
        }

        void MyRemovedPreExecutionHandler(object? sender, KernelRunningEventArgs e)
        {
            Console.WriteLine("Pre Execution Handler - Should not trigger");
            e.Cancel = true;
        }

        void MyPreHandler2(object? sender, KernelRunningEventArgs e)
        {
            Console.WriteLine($"Pre Execution Handler 2 - Prompt Token: {GPT3Tokenizer.Encode(e.Prompt!).Count}");
        }

        void MyPostExecutionHandler(object? sender, KernelRanEventArgs e)
        {
            Console.WriteLine($"Post Execution Handler - Total Tokens: {e.SKContext.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
        }

        kernel.FunctionInvoking += MyPreHandler;
        kernel.FunctionInvoking += MyPreHandler2;
        kernel.FunctionInvoking += MyRemovedPreExecutionHandler;
        kernel.FunctionInvoking -= MyRemovedPreExecutionHandler;

        kernel.FunctionInvoked += MyPostExecutionHandler;

        var result = await kernel.RunAsync(input, excuseFunction);
        Console.WriteLine($"Function Result: {result}");

        // Adding new inline handler to cancel/prevent function execution
        kernel.FunctionInvoking += (object? sender, KernelRunningEventArgs e) =>
        {
            Console.WriteLine("Pre Execution Handler - Cancel function execution");

            e.Cancel = true;
        };

        result = await kernel.RunAsync(input, excuseFunction);

        Console.WriteLine($"Function Not Executed (Result equals Input): {result.Result == input}");
    }
}
