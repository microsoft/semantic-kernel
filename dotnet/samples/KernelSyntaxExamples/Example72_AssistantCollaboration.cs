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
    //private const string OpenAIFunctionEnabledModel = "gpt-4-0613";
    private const string OpenAIFunctionEnabledModel = "gpt-4-1106-preview";

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

        // Explicit collaboration
        //await RunCollaborationAsync();

        // Coordinate collaboration as plugin agents (equivalent to previous case - shared thread)
        //await RunAsPluginsSharedThreadAsync();

        // Coordinate collaboration as plugin agents (not equivalent - delegate to separate thread)
        await RunAsPluginsManagerModelAsync();
    }

    /// <summary>
    /// Show how two assistants are able to collaborate as agents on a single thread.
    /// </summary>
    private static async Task RunCollaborationAsync()
    {
        Console.WriteLine("======== Run:Collaboration ========");
        IAssistant? copyWriter = null;
        IAssistant? artDirector = null;
        IChatThread? thread = null;
        try
        {
            // Create copy-writer assistant to generate ideas
            copyWriter = await CreateCopyWriterAsync();
            // Create art-director assistant to review ideas, provide feedback and final approval
            artDirector = await CreateArtDirectorAsync();
            // Create collaboration thread.
            thread = await copyWriter.NewThreadAsync();

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("maps made out of egg cartons.");
            DisplayMessage(messageUser);

            bool isComplete = false;
            while (!isComplete)
            {
                // Initiate copy-writer input
                var assistantMessages = await thread.InvokeAsync(copyWriter);
                DisplayMessages(assistantMessages);

                // Initiate art-director input
                assistantMessages = await thread.InvokeAsync(artDirector);
                DisplayMessages(assistantMessages);

                // Evaluate if goal is met.
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
    /// Show how assistants can collaborate as agents using the plug-in model.
    /// </summary>
    private static async Task RunAsPluginsSharedThreadAsync()
    {
        Console.WriteLine("======== Run:AsPlugins ========");
        IAssistant? copyWriter = null;
        IAssistant? artDirector = null;
        IAssistant? coordinator = null;
        IChatThread? thread = null;

        try
        {
            // Create copy-writer assistant to generate ideas
            copyWriter = await CreateCopyWriterAsync();
            // Create art-director assistant to review ideas, provide feedback and final approval
            artDirector = await CreateArtDirectorAsync();
            // Create coordinator assistant to oversee collaboration
            coordinator =
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Coordinate the repeated interaction between a copy-writer and an art-director on a single thread until the art-director approves the copy.  First call the copywriter.  After that, have the art-director review the copy.  Respond with the copy when approved by the art-director and summarize why it is good.")
                    .WithPlugin(copyWriter.AsPlugin())
                    .WithPlugin(artDirector.AsPlugin())
                    .BuildAsync();

            // Create top-level thread.
            thread = await coordinator.NewThreadAsync();
            Console.WriteLine($"[{thread.Id}]");

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("maps made out of egg cartons.").ConfigureAwait(true);
            DisplayMessage(messageUser);

            // Retrieve the final response.  This drives the interaction between the copy-writer and the art-director.
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

    /// <summary>
    /// Show how assistants can collaborate as agents using the plug-in model.
    /// </summary>
    private static async Task RunAsPluginsManagerModelAsync()
    {
        Console.WriteLine("======== Run:AsPlugins ========");
        IAssistant? copyWriter = null;
        IAssistant? artDirector = null;
        IChatThread? thread = null;

        try
        {
            // Create art-director assistant to review ideas, provide feedback and final approval
            artDirector = await CreateArtDirectorAsync();
            // Create copy-writer assistant to generate ideas
            copyWriter = await CreateCopyWriterAsync(artDirector);

            // Create top-level thread.
            thread = await artDirector.NewThreadAsync();
            Console.WriteLine($"[{thread.Id}]");

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("maps made out of egg cartons.").ConfigureAwait(true);
            DisplayMessage(messageUser);

            // Retrieve the final response.  This drives the interaction between the copy-writer and the art-director.
            var assistantMessages = await thread.InvokeAsync(artDirector).ConfigureAwait(true);
            DisplayMessages(assistantMessages);
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

    private static Task<IAssistant> CreateCopyWriterAsync(IAssistant? assistant = null)
    {
        return
            new AssistantBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .WithInstructions("You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.")
                .WithName("Copywriter")
                .WithDescription("Copywriter")
                .WithPlugin(assistant?.AsPlugin())
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
