// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase complex Open AI Assistant interactions using semantic kernel.
/// </summary>
public static class Example72_AssistantCollaboration
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
        Console.WriteLine("======== Example73_AssistantCollaboration ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        // $$$
        //await RunCollaborationAsync();

        // $$$
        await RunAsPluginsAsync();
    }

    /// <summary>
    /// $$$
    /// </summary>
    private static async Task RunCollaborationAsync()
    {
        Console.WriteLine("======== Run:Collaboration ========");
        IAssistant? copyWriter = null;
        IAssistant? artDirector = null;
        IChatThread? thread = null;
        try
        {
            copyWriter = await CreateCopyWriterAsync();
            artDirector = await CreateArtDirectorAsync();
            thread = await copyWriter.NewThreadAsync();

            var messageUser = await thread.AddUserMessageAsync("maps made out of egg cartons.");
            DisplayMessage(messageUser);

            bool isComplete = false;
            while (!isComplete)
            {
                var assistantMessages = await thread.InvokeAsync(copyWriter);
                DisplayMessages(assistantMessages);

                assistantMessages = await thread.InvokeAsync(artDirector);
                DisplayMessages(assistantMessages);

                if (assistantMessages.First().Content.Contains("PRINT IT", StringComparison.OrdinalIgnoreCase)) // $$$ BETTER
                {
                    isComplete = true;
                }
            }
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(
                thread?.DeleteAsync() ?? Task.CompletedTask,
                artDirector?.DeleteAsync() ?? Task.CompletedTask,
                copyWriter?.DeleteAsync() ?? Task.CompletedTask);
        }
    }

    /// <summary>
    /// $$$
    /// </summary>
    private static async Task RunAsPluginsAsync()
    {
        Console.WriteLine("======== Run:AsPlugins ========");
        IAssistant? copyWriter = null;
        IAssistant? artDirector = null;
        IAssistant? coordinator = null;
        IChatThread? thread = null;

        try
        {
            copyWriter = await CreateCopyWriterAsync();
            artDirector = await CreateArtDirectorAsync();

            thread = await copyWriter.NewThreadAsync(); // $$$ OTHER
            Console.WriteLine($"[{thread.Id}]");
            coordinator =
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Coordinate the repeated interaction between a copy-writer and an art-director on a single thread until the art-director approves the copy.  First call the copywriter, then have the art-director review the copy.  Respond with the copy when approved by the art-director and summarize why it is good.")
                    .WithPlugin(copyWriter.AsPlugin())
                    .WithPlugin(artDirector.AsPlugin())
                    .BuildAsync();

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("maps made out of egg cartons.").ConfigureAwait(true);
            DisplayMessage(messageUser);

            // Retrieve the assistant response
            var assistantMessages = await thread.InvokeAsync(coordinator).ConfigureAwait(true);
            DisplayMessages(assistantMessages);
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(
                thread?.DeleteAsync() ?? Task.CompletedTask,
                artDirector?.DeleteAsync() ?? Task.CompletedTask,
                copyWriter?.DeleteAsync() ?? Task.CompletedTask,
                coordinator?.DeleteAsync() ?? Task.CompletedTask);
        }
    }

    private static Task<IAssistant> CreateCopyWriterAsync()
    {
        return
            new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .WithInstructions("You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.")
                .WithName("Copywriter")
                .WithDescription("Copywriter")
                .BuildAsync();
    }

    private static Task<IAssistant> CreateArtDirectorAsync()
    {
        return
            new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .WithInstructions("You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to provide insight on how to refine suggested copy without example.  Always respond to the most recent message by evaluating and providing critique without example.  If copy is acceptable and meets your criteria, say: PRINT IT.")
                .WithName("Art Director")
                .WithDescription("Art Director")
                .BuildAsync();
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
