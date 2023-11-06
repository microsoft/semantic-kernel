// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

/**
 * This example shows how to use chat completion prompts.
 */
// ReSharper disable once InconsistentNaming
public static class Example63_ChatCompletionPrompts
{
    public static async Task RunAsync()
    {
        const string TextPrompt = "What is Seattle?";
        const string ChatPrompt = @"
            <message role=""user"">What is Seattle?</message>
            <message role=""system"">Respond with JSON.</message>
        ";

        var kernel = new KernelBuilder()
            .WithOpenAIChatCompletionService(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var textSemanticFunction = kernel.CreateSemanticFunction(TextPrompt);
        var chatSemanticFunction = kernel.CreateSemanticFunction(ChatPrompt);

        var textKernelResult = await kernel.RunAsync(textSemanticFunction);
        var chatKernelResult = await kernel.RunAsync(chatSemanticFunction);

        Console.WriteLine(textKernelResult);
        Console.WriteLine(chatKernelResult);
    }
}
