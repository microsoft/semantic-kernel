// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase hiearchical Open AI Assistant interactions using semantic kernel.
/// </summary>
public static class Example73_AssistantAuthoring
{
    /// <summary>
    /// Specific model is required that supports assistants and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-0613";

    /// <summary>
    /// Show how to combine coordinate multiple assistants.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example73_AssistantAuthoring ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        await Task.Delay(0);
    }
}
