// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Orchestration;
using Plugins;
using Resources;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase Open AI Assistant integration with semantic kernel.
/// </summary>
public static class Example70_Assistant
{
    private const string OpenAIFunctionEnabledModel = "gpt-3.5-turbo-1106";

    /// <summary>
    /// Show how to define an use a single assistant using multiple patterns.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example70_Assistant ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        await RunSimpleChatAsync();

        await RunWithNativeFunctionsAsync();

        await RunWithSemanticFunctionsAsync();

        await RunAsFunctionAsync();
    }

    private static async Task RunSimpleChatAsync()
    {
        Console.WriteLine("======== Run:SimpleChat ========");

        await ChatAsync(
            "Assistants.ParrotAssistant.yaml",
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    private static async Task RunWithNativeFunctionsAsync()
    {
        Console.WriteLine("======== Run:WithNativeFunctions ========");

        ISKPlugin plugin = KernelPluginFactory.CreateFromObject<MenuPlugin>();

        await ChatAsync(
            "Assistants.ToolAssistant.yaml",
            plugin,
            "Hello",
            "What is the special soup?",
            "What is the special drink?",
            "Thank you!");
    }

    private static async Task RunWithSemanticFunctionsAsync()
    {
        Console.WriteLine("======== Run:WithSemanticFunctions ========");

        var plugin = new SKPlugin("test");
        plugin.AddFunctionFromPrompt(
             "Correct any misspelling or gramatical errors provided in input: {{$input}}",
              functionName: "spellChecker",
              description: "Correct the spelling for the user input."
        );

        await ChatAsync(
            "Assistants.ToolAssistant.yaml",
            plugin,
            "Hello",
            "Is this spelled correctly: exercize",
            "What is the special soup?",
            "Thank you!");
    }

    private static async Task RunAsFunctionAsync()
    {
        Console.WriteLine("======== Run:AsFunction ========");

        var assistant =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                OpenAIFunctionEnabledModel,
                EmbeddedResource.Read("Assistants.ParrotAssistant.yaml"));

        Kernel kernel = new KernelBuilder().Build();

        var assistants = kernel.ImportPluginFromObject(assistant, assistant.Id);

        var variables = new ContextVariables
        {
            ["input"] = "Practice makes perfect."
        };
        var result = await kernel.InvokeAsync(assistants.Single(), variables);
        var resultValue = result.GetValue<string>();

        var response = JsonSerializer.Deserialize<AssistantResponse>(resultValue ?? string.Empty);
        Console.WriteLine(
            response?.Response ??
            $"No response from assistant: {assistant.Id}");
    }

    private static Task ChatAsync(
         string resourcePath,
         params string[] messages)
    {
        return ChatAsync(resourcePath, null, messages);
    }

    private static async Task ChatAsync(
        string resourcePath,
        ISKPlugin? plugin,
        params string[] messages)
    {
        var definition = EmbeddedResource.Read(resourcePath);

        var plugins = plugin == null ? new SKPluginCollection() : new SKPluginCollection() { plugin };

        var assistant =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                OpenAIFunctionEnabledModel,
                definition,
                plugins);

        Console.WriteLine($"[{assistant.Id}]");

        var thread = await assistant.NewThreadAsync();
        foreach (var message in messages)
        {
            var messageUser = await thread.AddUserMessageAsync(message).ConfigureAwait(true);
            DisplayMessage(messageUser);

            var assistantMessages = await thread.InvokeAsync(assistant).ConfigureAwait(true);
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
