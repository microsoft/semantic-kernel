// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Resources;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase complex Open AI Assistant interactions using semantic kernel.
/// </summary>
public static class Example71_AssistantDelegation
{
    private const string OpenAIFunctionEnabledModel = "gpt-3.5-turbo-1106";

    /// <summary>
    /// Show how to combine coordinate multiple assistants.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example71_AssistantDelegation ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        await RunWithDelegationAsync();
    }

    private static async Task RunWithDelegationAsync()
    {
        Console.WriteLine("======== Example71_AssistantDelegation ========");

        var definition = EmbeddedResource.Read("Assistants.ToolAssistant.yaml");
        var assistant =
            await AssistantBuilder.FromTemplateAsync(
                TestConfiguration.OpenAI.ApiKey,
                OpenAIFunctionEnabledModel,
                definition);
    }
}
