// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
/**
* This example shows how to load a <see cref="KernelPlugin"/> instances.
*/
public static class Step2_Add_Plugins
{
    /// <summary>
    /// Shows different ways to load a <see cref="KernelPlugin"/> instances.
    /// </summary>
    public static async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<TimeInformation>();
        Kernel kernel = kernelBuilder.Build();

        // Example 1. Invoke the kernel with a prompt that asks the AI for inromation it cannot provide and may hallucinate
        Console.WriteLine(await kernel.InvokePromptAsync("How many days until Christmas?"));

        // Example 2. Invoke the kernel with a templated prompt that invokes a plugin and display the result
        Console.WriteLine(await kernel.InvokePromptAsync("The current time is {{TimeInformation.GetCurrentUtcTime}}. How many days until Christmas?"));

        // Example 3. Invoke the kernel with a prompt and allow the AI to automatically invoke functions
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        Console.WriteLine(await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.", new(settings)));
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation
    {
        [KernelFunction]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");
    }
}
