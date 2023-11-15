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

        IKernel bootstraper = new KernelBuilder().Build();

        var functions = bootstraper.ImportFunctions(new MenuPlugin(), nameof(MenuPlugin));

        var assistant1 =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                model: OpenAIFunctionEnabledModel,
                template: EmbeddedResource.Read("Assistants.ToolAssistant.yaml"),
                functions: functions.Values);

        var assistant2 =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                model: OpenAIFunctionEnabledModel,
                template: EmbeddedResource.Read("Assistants.ParrotAssistant.yaml"));

        var helperAssistants = Import(assistant1, assistant2).ToArray();

        var assistant3 =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                model: OpenAIFunctionEnabledModel,
                template: EmbeddedResource.Read("Assistants.ToolAssistant.yaml"),
                functions: helperAssistants);

        await ChatAsync(
            assistant3,
            "What's on the menu?",
            "Can you talk like pirate?",
            "Thank you");

        IEnumerable<ISKFunction> Import(params IAssistant[] assistants)
        {
            foreach (var assistant in assistants)
            {
                var functions = bootstraper.ImportFunctions(assistant, assistant.Id);
                foreach (var function in functions.Values)
                {
                    yield return function;
                }
            }
        }
    }
    private static async Task ChatAsync(IAssistant assistant, params string[] messages)
    {
        var thread = await assistant.NewThreadAsync();
        foreach (var message in messages)
        {
            var messageUser = await thread.AddUserMessageAsync(message).ConfigureAwait(true);
            DisplayMessage(messageUser);

            var assistantMessages = await thread.InvokeAsync(assistant).ConfigureAwait(true);
            DisplayMessage(assistantMessages);
        }
    }

    private static void DisplayMessage(IEnumerable<IChatMessage> messages)
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
