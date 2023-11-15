// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Orchestration;
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

        //await RunSimpleChatAsync();

        //await RunWithNativeFunctionsAsync();

        //await RunWithSemanticFunctionsAsync();

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

        IKernel bootstraper = new KernelBuilder().Build();

        var functions = bootstraper.ImportFunctions(new MenuPlugin(), nameof(MenuPlugin));

        await ChatAsync(
            "Assistants.ToolAssistant.yaml",
            functions.Values,
            "Hello",
            "What is the special soup?",
            "What is the special drink?",
            "Thank you!");
    }

    private static async Task RunWithSemanticFunctionsAsync()
    {
        Console.WriteLine("======== Run:WithSemanticFunctions ========");

        IKernel bootstraper = new KernelBuilder().Build();

        var functions =
            new[]
            {
                bootstraper.CreateSemanticFunction(
                    "Correct any misspelling or gramatical errors provided in input: {{$input}}",
                    functionName: "spellChecker",
                    pluginName: "test",
                    description: "Correct the spelling for the user input."),
            };

        await ChatAsync(
            "Assistants.ToolAssistant.yaml",
            functions,
            "Hello",
            "Is this spelled correctly: exercize",
            "What is the special soup?",
            "Thank you!");
    }

    private static async Task RunAsFunctionAsync()
    {
        Console.WriteLine("======== Run:AsFunction ========");

        var definition = EmbeddedResource.Read("Assistants.ParrotAssistant.yaml");
        var assistant =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                OpenAIFunctionEnabledModel,
                definition);

        IKernel bootstraper = new KernelBuilder().Build();

        var assistants = bootstraper.ImportFunctions(assistant, "Assistants");

        var variables = new ContextVariables
        {
            ["input"] = "Practice makes perfect."
        };
        var result = await bootstraper.RunAsync(assistants.Single().Value, variables);
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
        IEnumerable<ISKFunction>? functions,
        params string[] messages)
    {
        var definition = EmbeddedResource.Read(resourcePath);

        var assistant =
            await AssistantBuilder.FromDefinitionAsync(
                TestConfiguration.OpenAI.ApiKey,
                OpenAIFunctionEnabledModel,
                definition,
                functions);

        Console.WriteLine($"[{assistant.Id}]");

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
        Console.WriteLine($"# {message.Content}");
    }

    private sealed class MenuPlugin
    {
        [SKFunction, Description("Provides a list of specials from the menu.")]
        public string GetSpecials()
        {
            return @"
Special Soup: Clam Chowder
Special Salad: Cobb Chowder
Special Drink: Chai Tea
";
        }

        [SKFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem)
        {
            return "$9.99";
        }
    }
}
