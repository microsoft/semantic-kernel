// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.ProcessOrchestrator.Models;

namespace ProcessFramework.Aspire.ProcessOrchestrator.Steps;

public class TranslateStep : KernelProcessStep
{
    public static class Functions
    {
        public const string Translate = nameof(Translate);
    }

    [KernelFunction(Functions.Translate)]
    public async ValueTask TranslateAsync(KernelProcessStepContext context, Kernel kernel, string textToTranslate)
    {
        var translatorAgentHttpClient = kernel.GetRequiredService<TranslatorAgentHttpClient>();
        var translatedText = await translatorAgentHttpClient.TranslateAsync(textToTranslate);
        Console.WriteLine($"Translated text: {translatedText}");
        await context.EmitEventAsync(new() { Id = ProcessEvents.DocumentTranslated, Data = translatedText });
    }
}
