// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase hiearchical Open AI Assistant interactions using semantic kernel.
/// </summary>
public static class Example73_AssistantAuthoring
{
    /// <summary>
    /// Specific model is required that supports assistants and parallel function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-1106-preview";

    // Track assistants for clean-up
    private static readonly List<IAssistant> s_assistants = new();

    /// <summary>
    /// Show how to combine coordinate multiple assistants.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example73_AssistantAuthoring ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        // Run demo by invoking assistant directly
        await RunAssistantAsync();

        // Run demo by invoking assistant as a plugin
        await RunAsPluginAsync();
    }

    private static async Task RunAssistantAsync()
    {
        try
        {
            // Initialize the assistant with tools
            IAssistant articleGenerator = await CreateArticleGeneratorAsync();

            // "Stream" messages as they become available
            await foreach (IChatMessage message in articleGenerator.InvokeAsync("Thai food is the best in the world"))
            {
                Console.WriteLine($"[{message.Id}]");
                Console.WriteLine($"# {message.Role}: {message.Content}");
            }
        }
        finally
        {
            await Task.WhenAll(s_assistants.Select(a => a.DeleteAsync()));
        }
    }

    private static async Task RunAsPluginAsync()
    {
        try
        {
            // Initialize the assistant with tools
            IAssistant articleGenerator = await CreateArticleGeneratorAsync();

            // Invoke as a plugin function
            string response = await articleGenerator.AsPlugin().InvokeAsync("Thai food is the best in the world");

            // Display final result
            Console.WriteLine(response);
        }
        finally
        {
            await Task.WhenAll(s_assistants.Select(a => a.DeleteAsync()));
        }
    }

    private static async Task<IAssistant> CreateArticleGeneratorAsync()
    {
        // Initialize the outline assistant
        var outlineGenerator = await CreateOutlineGeneratorAsync();
        // Initialize the research assistant
        var sectionGenerator = await CreateResearchGeneratorAsync();

        // Initialize assistant so that it may be automatically deleted.
        return
            Track(
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You write concise opinionated articles that are published online.  Use an outline to generate an article with one section of prose for each top-level outline element.  Each section is based on research with a maximum of 120 words.")
                    .WithName("Article Author")
                    .WithDescription("Author an article on a given topic.")
                    .WithPlugin(outlineGenerator.AsPlugin())
                    .WithPlugin(sectionGenerator.AsPlugin())
                    .BuildAsync());
    }

    private static async Task<IAssistant> CreateOutlineGeneratorAsync()
    {
        // Initialize assistant so that it may be automatically deleted.
        return
            Track(
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Produce an single-level outline (no child elements) based on the given topic with at most 3 sections.")
                    .WithName("Outline Generator")
                    .WithDescription("Generate an outline.")
                    .BuildAsync());
    }

    private async static Task<IAssistant> CreateResearchGeneratorAsync()
    {
        // Initialize assistant so that it may be automatically deleted.
        return
            Track(
                await new AssistantBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Provide insightful research that supports the given topic based on your knowledge of the outline topic.")
                    .WithName("Researcher")
                    .WithDescription("Author research summary.")
                    .BuildAsync());
    }

    private static IAssistant Track(IAssistant assistant)
    {
        s_assistants.Add(assistant);

        return assistant;
    }
}
