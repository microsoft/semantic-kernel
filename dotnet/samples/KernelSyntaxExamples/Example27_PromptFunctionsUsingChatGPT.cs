// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using RepoUtils;

/**
 * This example shows how to use GPT3.5 Chat model for prompts and prompt functions.
 */
// ReSharper disable once InconsistentNaming
public static class Example27_PromptFunctionsUsingChatGPT
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Using Chat GPT model for text completion ========");

        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        var func = kernel.CreateFunctionFromPrompt(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync(kernel, "Jupiter");
        Console.WriteLine(result.GetValue<string>());

        /*
        Output:
           - Saturn
           - Uranus
        */
    }
}
