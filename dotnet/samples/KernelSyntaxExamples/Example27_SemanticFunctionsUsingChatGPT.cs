// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

/**
 * This example shows how to use GPT3.5 Chat model for prompts and semantic functions.
 */

// ReSharper disable once InconsistentNaming
public static class Example27_SemanticFunctionsUsingChatGPT
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Using Chat GPT model for text completion ========");

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            // Note: we use Chat Completion and GPT 3.5 Turbo
            .WithAzureChatCompletionService("gpt-35-turbo", "https://....openai.azure.com/", "...API KEY...")
            .Build();

        var func = kernel.CreateSemanticFunction(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync(input: "Jupiter");
        Console.WriteLine(result);

        /*
        Output:
           - Saturn
           - Uranus
        */
    }
}
