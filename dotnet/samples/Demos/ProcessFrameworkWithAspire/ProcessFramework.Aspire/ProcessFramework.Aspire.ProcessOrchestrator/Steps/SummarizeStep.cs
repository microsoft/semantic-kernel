// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.ProcessOrchestrator.Models;

namespace ProcessFramework.Aspire.ProcessOrchestrator.Steps;

public class SummarizeStep : KernelProcessStep
{
    public static class Functions
    {
        public const string Summarize = nameof(Summarize);
    }

    [KernelFunction(Functions.Summarize)]
    public async ValueTask SummarizeAsync(KernelProcessStepContext context, Kernel kernel, string textToSummarize)
    {
        var summaryAgentHttpClient = kernel.GetRequiredService<SummaryAgentHttpClient>();
        var summarizedText = await summaryAgentHttpClient.SummarizeAsync(textToSummarize);
        Console.WriteLine($"Summarized text: {summarizedText}");
        await context.EmitEventAsync(new() { Id = ProcessEvents.DocumentSummarized, Data = summarizedText });
    }
}
