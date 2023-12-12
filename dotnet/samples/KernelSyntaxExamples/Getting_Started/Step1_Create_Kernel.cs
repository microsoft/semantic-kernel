// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

/**
 * This example shows how to create and use a <see cref="Kernel"/>.
 */
public static class Step1_Create_Kernel
{
    /// <summary>
    /// Show how to create a <see cref="Kernel"/> and use it to execute prompts.
    /// </summary>
    public static async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Example 1. Invoke the kernel with a prompt and display the result
        Console.WriteLine(await kernel.InvokePromptAsync("What color is the sky?"));

        // Example 2. Invoke the kernel with a templated prompt and display the result
        KernelArguments arguments = new() { { "topic", "sea" } };
        Console.WriteLine(await kernel.InvokePromptAsync("What color is the {{$topic}}?", arguments));

        // Example 3. Invoke the kernel with a templated prompt and stream the results to the display
        await foreach (var update in kernel.InvokePromptStreamingAsync("What color is the {{$topic}}? Provide a detailed explanation.", arguments))
        {
            Console.Write(update);
        }
    }
}
