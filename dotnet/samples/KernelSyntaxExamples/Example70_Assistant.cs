// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Plugins;
using Resources;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase Open AI Assistant integration with semantic kernel:
/// https://platform.openai.com/docs/api-reference/assistants
/// </summary>
public static class Example70_Assistant
{
    /// <summary>
    /// Specific model is required that supports assistants and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
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

        // "Hello assistant"
        await RunSimpleChatAsync();

        // Run assistant with "method" tool/function
        await RunWithMethodFunctionsAsync();

        // Run assistant with "prompt" tool/function
        await RunWithPromptFunctionsAsync();

        // Run assistant as function
        await RunAsFunctionAsync();
    }

    /// <summary>
    /// Chat using the "Parrot" assistant.
    /// Tools/functions: None
    /// </summary>
    private static async Task RunSimpleChatAsync()
    {
        Console.WriteLine("======== Run:SimpleChat ========");

        // Call the common chat-loop
        await ChatAsync(
            "Assistants.ParrotAssistant.yaml", // Defined under ./Resources/Assistants
            plugin: null, // No plugin
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    /// <summary>
    /// Chat using the "Tool" assistant and a method function.
    /// Tools/functions: MenuPlugin
    /// </summary>
    private static async Task RunWithMethodFunctionsAsync()
    {
        Console.WriteLine("======== Run:WithMethodFunctions ========");

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        // Call the common chat-loop
        await ChatAsync(
            "Assistants.ToolAssistant.yaml", // Defined under ./Resources/Assistants
            plugin,
            "Hello",
            "What is the special soup?",
            "What is the special drink?",
            "Thank you!");
    }

    /// <summary>
    /// Chat using the "Tool" assistant and a prompt function.
    /// Tools/functions: spellChecker prompt function
    /// </summary>
    private static async Task RunWithPromptFunctionsAsync()
    {
        Console.WriteLine("======== WithPromptFunctions ========");

        // Create a prompt function.
        var function = KernelFunctionFactory.CreateFromPrompt(
             "Correct any misspelling or gramatical errors provided in input: {{$input}}",
              functionName: "spellChecker",
              description: "Correct the spelling for the user input."
        );
        var plugin = KernelPluginFactory.CreateFromFunctions("spelling", "Spelling functions", new[] { function });

        // Call the common chat-loop
        await ChatAsync(
            "Assistants.ToolAssistant.yaml", // Defined under ./Resources/Assistants
            plugin,
            "Hello",
            "Is this spelled correctly: exercize",
            "What is the special soup?",
            "Thank you!");
    }

    /// <summary>
    /// Invoke assistant just like any other <see cref="KernelFunction"/>.
    /// </summary>
    private static async Task RunAsFunctionAsync()
    {
        Console.WriteLine("======== Run:AsFunction ========");

        // Create parrot assistant, same as the other cases.
        var assistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(EmbeddedResource.Read("Assistants.ParrotAssistant.yaml"))
                .BuildAsync();

        try
        {
            // Invoke assistant plugin.
            var response = await assistant.AsPlugin().InvokeAsync("Practice makes perfect.");

            // Display result.
            Console.WriteLine(response ?? $"No response from assistant: {assistant.Id}");
        }
        finally
        {
            // Clean-up (storage costs $)
            await assistant.DeleteAsync();
        }
    }

    /// <summary>
    /// Common chat loop used for: RunSimpleChatAsync, RunWithMethodFunctionsAsync, and RunWithPromptFunctionsAsync.
    /// 1. Reads assistant definition from"resourcePath" parameter.
    /// 2. Initializes assistant with definition and the specified "plugin".
    /// 3. Display the assistant identifier
    /// 4. Create a chat-thread
    /// 5. Process the provided "messages" on the chat-thread
    /// </summary>
    private static async Task ChatAsync(
        string resourcePath,
        KernelPlugin? plugin = null,
        params string[] messages)
    {
        // Read assistant resource
        var definition = EmbeddedResource.Read(resourcePath);

        // Create assistant
        var assistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(definition)
                .WithPlugin(plugin)
                .BuildAsync();

        // Create chat thread.  Note: Thread is not bound to a single assistant.
        var thread = await assistant.NewThreadAsync();
        try
        {
            // Display assistant identifier.
            Console.WriteLine($"[{assistant.Id}]");

            // Process each user message and assistant response.
            foreach (var response in messages.Select(m => thread.InvokeAsync(assistant, m)))
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
                assistant.DeleteAsync());
        }
    }
}
