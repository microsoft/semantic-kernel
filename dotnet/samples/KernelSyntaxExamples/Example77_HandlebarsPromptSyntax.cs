// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using System.Text.Json;
using System.Diagnostics;
using System.Collections.Generic;

namespace KernelSyntaxExamples;

// ReSharper disable once InconsistentNaming
public static class Example77_HandlebarsPromptSyntax
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== LLMPrompts ========");

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();



    }
}
