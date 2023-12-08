// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Plugins;
using Resources;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase complex Open AI Assistant interactions using semantic kernel.
/// </summary>
public static class Example71_AssistantDelegation
{
    /// <summary>
    /// Specific model is required that supports assistants and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-3.5-turbo-1106";

    // Track assistants for clean-up
    private static readonly List<IAssistant> s_assistants = new();

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

        IChatThread? thread = null;

        try
        {
            var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
            var menuAssistant =
                Track(
                    await new AssistantBuilder()
                        .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                        .FromTemplate(EmbeddedResource.Read("Assistants.ToolAssistant.yaml"))
                        .WithDescription("Answer questions about how the menu uses the tool.")
                        .WithPlugin(plugin)
                        .BuildAsync());

            var parrotAssistant =
                Track(
                    await new AssistantBuilder()
                        .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                        .FromTemplate(EmbeddedResource.Read("Assistants.ParrotAssistant.yaml"))
                        .BuildAsync());

            var toolAssistant =
                Track(
                    await new AssistantBuilder()
                        .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                        .FromTemplate(EmbeddedResource.Read("Assistants.ToolAssistant.yaml"))
                        .WithPlugin(parrotAssistant.AsPlugin())
                        .WithPlugin(menuAssistant.AsPlugin())
                        .BuildAsync());

            var messages = new string[]
            {
                "What's on the menu?",
                "Can you talk like pirate?",
                "Thank you",
            };

            thread = await toolAssistant.NewThreadAsync();
            foreach (var response in messages.Select(m => thread.InvokeAsync(toolAssistant, m)))
            {
                await foreach (var message in response)
                {
                    Console.WriteLine($"[{message.Id}]");
                    Console.WriteLine($"# {message.Role}: {message.Content}");
                }
            }
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(
                thread?.DeleteAsync() ?? Task.CompletedTask,
                Task.WhenAll(s_assistants.Select(a => a.DeleteAsync())));
        }
    }

    private static IAssistant Track(IAssistant assistant)
    {
        s_assistants.Add(assistant);

        return assistant;
    }
}
