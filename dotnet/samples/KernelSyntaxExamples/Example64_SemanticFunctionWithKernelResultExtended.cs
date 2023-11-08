// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;
using Microsoft.SemanticKernel.AI;
using System.Diagnostics;

// ReSharper disable once InconsistentNaming
public static class Example64_SemanticFunctionWithKernelResultExtended
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== LLMPrompts ========");

        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, openAIApiKey)
            .Build();

        // Load semantic plugins defined with prompt templates
        string folder = RepoFiles.SamplePluginsPath();

        var summarizeFunctions = kernel.ImportSemanticFunctionsFromDirectory(folder, "SummarizePlugin");

        // Run
        var ask = "In programming, a \"strongly typed\" class refers to a class that enforces strict type constraints on its members and operations. This means that the class will only allow instances of types that are explicitly defined as valid by the class's type system, and any attempt to create an instance of the class with an invalid type will result in a compile-time error.\n\nOn the other hand, a \"sealed\" class is one that does not expose all of its internal objects directly to the outside world. In other words, the class provides a way for external code to interact with its internal objects only through a controlled interface, such as methods or properties.";

        // Time it
        var sw = new Stopwatch();
        sw.Start();

        var result = await kernel.RunAsync(
            ask,
            summarizeFunctions["Summarize"]);

        // Stop the timer
        sw.Stop();

        var kernelSummarizeResult = new KernelResultExtSummarize(
            result!,
            sw.ElapsedMilliseconds);

        Console.WriteLine(ask + "\n");
        Console.WriteLine($"Summary: {kernelSummarizeResult.Summary} \n");
        Console.WriteLine($"Milliseconds: {kernelSummarizeResult.ExecutionTimeInMilliseconds} \n");
        Console.WriteLine($"Total Tokens: {kernelSummarizeResult.TokenCounts!.TotalTokens} \n");
    }
}

public record KernelResultExtSummarize : KernelResultExtended
{
    /// <summary>
    /// here is the perfect place to transform the result into a strongly typed object
    /// IE: here is a plain string, but if the model output is a JSON object, we can
    /// parse it here and return a strongly typed object instead of a string.
    /// Inmutable, fully validated and checked right out of the model.
    /// </summary>
    public string Summary { get; init; }

    public long ExecutionTimeInMilliseconds { get; init; }

    public KernelResultExtSummarize(
        KernelResult kernelResult,
        long executionTimeInMilliseconds)
        : base(kernelResult)
    {
        this.Summary = this.Result;
        this.ExecutionTimeInMilliseconds = executionTimeInMilliseconds;
        this.TokenCounts = this.ParseTokenCountsFromKernelResult();
    }

    private TokenCounts ParseTokenCountsFromKernelResult()
    {
        var modelResults = this.KernelResult.FunctionResults.SelectMany(
            l => l.GetModelResults() ?? Enumerable.Empty<ModelResult>());

        CompletionsUsage? Usage = modelResults.LastOrDefault()?.GetOpenAIChatResult()?.Usage;

        return new TokenCounts(
            CompletionTokens: Usage?.CompletionTokens ?? 0,
            PromptTokens: Usage?.PromptTokens ?? 0,
            TotalTokens: Usage?.TotalTokens ?? 0);
    }
}
