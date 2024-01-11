// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

public static class Step5_Chat_Prompt
{
    /// <summary>
    /// Show how to construct a chat prompt and invoke it.
    /// </summary>
    public static async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Invoke the kernel with a chat prompt and display the result
        string chatPrompt = @"
            <message role=""user"">What is Seattle?</message>
            <message role=""system"">Respond with JSON.</message>
        ";
        Console.WriteLine(await kernel.InvokePromptAsync(chatPrompt));
    }
}
