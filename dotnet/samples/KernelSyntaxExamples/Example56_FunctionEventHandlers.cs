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
public static class Example56_FunctionEventHandlers
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
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAITextCompletionService(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        const string functionPrompt = "Write a paragraph about: {{$input}}.";

        var excuseFunction = kernel.CreateSemanticFunction(
            functionPrompt,
            skillName: "MySkill",
            functionName: "Excuse",
            maxTokens: 100,
            temperature: 0.4,
            topP: 1);

        void MyPreHandler(object? sender, FunctionInvokingEventArgs e)
        {
            if (e is SemanticFunctionInvokingEventArgs se)
            {
                Console.WriteLine($"{se.FunctionView.SkillName}.{se.FunctionView.Name} : Pre Execution Handler - Rendered Prompt: {se.RenderedPrompt}");
            }
        }

        void MyRemovedPreExecutionHandler(object? sender, FunctionInvokingEventArgs e)
        {
            Console.WriteLine($"{e.FunctionView.SkillName}.{e.FunctionView.Name} : Pre Execution Handler - Should not trigger");
            e.Cancel();
        }

        void MyPreHandler2(object? sender, FunctionInvokingEventArgs e)
        {
            if (e is SemanticFunctionInvokingEventArgs se)
            {
                Console.WriteLine($"{se.FunctionView.SkillName}.{se.FunctionView.Name} : Pre Execution Handler 2 - Rendered Prompt Token: {GPT3Tokenizer.Encode(se.RenderedPrompt!).Count}");
            }
        }

        void MyPostExecutionHandler(object? sender, FunctionInvokedEventArgs e)
        {
            Console.WriteLine($"{e.FunctionView.SkillName}.{e.FunctionView.Name} : Post Execution Handler - Total Tokens: {e.SKContext.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
        }

        kernel.FunctionInvoking += MyPreHandler;
        kernel.FunctionInvoking += MyPreHandler2;
        kernel.FunctionInvoking += MyRemovedPreExecutionHandler;
        kernel.FunctionInvoking -= MyRemovedPreExecutionHandler;

        kernel.FunctionInvoked += MyPostExecutionHandler;

        const string input = "I missed the F1 final race";

        var result = await kernel.RunAsync(input, excuseFunction);
        Console.WriteLine($"Function Result: {result}");

        // Adding new inline handler to cancel/prevent function execution
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            Console.WriteLine($"{e.FunctionView.SkillName}.{e.FunctionView.Name} : Pre Execution Handler - Cancel function execution");

            e.Cancel();
        };

        result = await kernel.RunAsync(input, excuseFunction);

        Console.WriteLine($"Function Not Executed (Result equals Input): {result.Result == input}");
    }
}
