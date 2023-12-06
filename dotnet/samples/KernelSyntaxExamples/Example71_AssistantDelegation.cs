// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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

        var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        var menuAssistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(EmbeddedResource.Read("Assistants.ToolAssistant.yaml"))
                .WithDescription("Answer questions about how the menu uses the tool.")
                .WithPlugin(plugin)
                .BuildAsync();

        var parrotAssistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(EmbeddedResource.Read("Assistants.ParrotAssistant.yaml"))
                .BuildAsync();

        var toolAssistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(EmbeddedResource.Read("Assistants.ToolAssistant.yaml"))
                .WithPlugins(new[] { menuAssistant.AsPlugin(), parrotAssistant.AsPlugin() })
                .BuildAsync();

        var messages = new string[]
        {
            "What's on the menu?",
            "Can you talk like pirate?",
            "Thank you",
        };

        var thread = await toolAssistant.NewThreadAsync();
        foreach (var message in messages)
        {
            var messageUser = await thread.AddUserMessageAsync(message).ConfigureAwait(true);
            DisplayMessage(messageUser);

            var assistantMessages = await thread.InvokeAsync(toolAssistant).ConfigureAwait(true);
            DisplayMessages(assistantMessages);
        }
    }

    private static void DisplayMessages(IEnumerable<IChatMessage> messages)
    {
        foreach (var message in messages)
        {
            DisplayMessage(message);
        }
    }

    private static void DisplayMessage(IChatMessage message)
    {
        Console.WriteLine($"[{message.Id}]");
        Console.WriteLine($"# {message.Role}: {message.Content}");
    }
}
