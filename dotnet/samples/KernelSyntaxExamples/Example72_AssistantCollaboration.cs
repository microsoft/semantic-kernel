// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase complex Open AI Assistant collaboration using semantic kernel.
/// </summary>
public static class Example72_AssistantCollaboration
{
    /// <summary>
    /// Specific model is required that supports assistants and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-0613";

    // Track assistants for clean-up
    private static readonly List<IAssistant> s_assistants = new();

    /// <summary>
    /// Show how to combine and coordinate multiple assistants.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example72_AssistantCollaboration ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        // Explicit collaboration
        await RunCollaborationAsync();

        // Coordinate collaboration as plugin agents (equivalent to previous case - shared thread)
        await RunAsPluginsAsync();
    }

    /// <summary>
    /// Show how two assistants are able to collaborate as agents on a single thread.
    /// </summary>
    private static async Task RunCollaborationAsync()
    {
        Console.WriteLine("======== Run:Collaboration ========");
        IChatThread? thread = null;
        try
        {
            // Create copy-writer assistant to generate ideas
            var copyWriter = await CreateCopyWriterAsync();
            // Create art-director assistant to review ideas, provide feedback and final approval
            var artDirector = await CreateArtDirectorAsync();

            // Create collaboration thread to which both assistants add messages.
            thread = await copyWriter.NewThreadAsync();

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("concept: maps made out of egg cartons.");
            DisplayMessage(messageUser);

            bool isComplete = false;
            do
            {
                // Initiate copy-writer input
                var assistantMessages = await thread.InvokeAsync(copyWriter).ToArrayAsync();
                DisplayMessages(assistantMessages, copyWriter);

                // Initiate art-director input
                assistantMessages = await thread.InvokeAsync(artDirector).ToArrayAsync();
                DisplayMessages(assistantMessages, artDirector);

                // Evaluate if goal is met.
                if (assistantMessages.First().Content.Contains("PRINT IT", StringComparison.OrdinalIgnoreCase))
                {
                    isComplete = true;
                }
            }
            while (!isComplete);
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(s_assistants.Select(a => a.DeleteAsync()));
        }
    }

    /// <summary>
    /// Show how assistants can collaborate as agents using the plug-in model.
    /// </summary>
    /// <remarks>
    /// While this may achieve an equivalent result to <see cref="RunCollaborationAsync"/>,
    /// it is not using shared thread state for assistant interaction.
    /// </remarks>
    private static async Task RunAsPluginsAsync()
    {
        Console.WriteLine("======== Run:AsPlugins ========");
        try
        {
            // Create copy-writer assistant to generate ideas
            var copyWriter = await CreateCopyWriterAsync();
            // Create art-director assistant to review ideas, provide feedback and final approval
            var artDirector = await CreateArtDirectorAsync();

            // Create coordinator assistant to oversee collaboration
            var coordinator =
                Track(
                    await new AssistantBuilder()
                        .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                        .WithInstructions("Reply the provided concept and have the copy-writer generate an marketing idea (copy).  Then have the art-director reply to the copy-writer with a review of the copy.  Coordinate the repeated replies between the copy-writer and art-director until the art-director approves the copy.  Respond with the copy when approved by the art-director and summarize why it is good.")
                        .WithPlugin(copyWriter.AsPlugin())
                        .WithPlugin(artDirector.AsPlugin())
                        .BuildAsync());

            // Invoke as a plugin function
            var response = await coordinator.AsPlugin().InvokeAsync("concept: maps made out of egg cartons.");

            // Display final result
            Console.WriteLine(response);
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(s_assistants.Select(a => a.DeleteAsync()));
        }
    }

    private async static Task<IAssistant> CreateCopyWriterAsync(IAssistant? assistant = null)
    {
        return
            Track(
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.")
                    .WithName("Copywriter")
                    .WithDescription("Copywriter")
                    .WithPlugin(assistant?.AsPlugin())
                    .BuildAsync());
    }

    private async static Task<IAssistant> CreateArtDirectorAsync()
    {
        return
            Track(
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to provide insight on how to refine suggested copy without example.  Always respond to the most recent message by evaluating and providing critique without example.  Always repeat the copy at the beginning.  If copy is acceptable and meets your criteria, say: PRINT IT.")
                    .WithName("Art Director")
                    .WithDescription("Art Director")
                    .BuildAsync());
    }

    private static void DisplayMessages(IEnumerable<IChatMessage> messages, IAssistant? assistant = null)
    {
        foreach (var message in messages)
        {
            DisplayMessage(message, assistant);
        }
    }

    private static void DisplayMessage(IChatMessage message, IAssistant? assistant = null)
    {
        Console.WriteLine($"[{message.Id}]");
        if (assistant != null)
        {
            Console.WriteLine($"# {message.Role}: ({assistant.Name}) {message.Content}");
        }
        else
        {
            Console.WriteLine($"# {message.Role}: {message.Content}");
        }
    }

    private static IAssistant Track(IAssistant assistant)
    {
        s_assistants.Add(assistant);

        return assistant;
    }
}
