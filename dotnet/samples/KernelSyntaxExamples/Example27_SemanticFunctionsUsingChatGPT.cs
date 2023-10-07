// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        var func = kernel.CreateSemanticFunction(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync("Jupiter", kernel);
        Console.WriteLine(result.GetValue<string>());

        /*
        Output:
           - Saturn
           - Uranus
        */
    }
}
