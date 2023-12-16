// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase complex Open AI Agent collaboration using semantic kernel.
/// </summary>
public static class Example72_AgentCollaboration
{
    /// <summary>
    /// Specific model is required that supports agents and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-0613";

    // Track agents for clean-up
    private static readonly List<IAgent> s_agents = new();

    /// <summary>
    /// Show how to combine and coordinate multiple agents.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example72_AgentCollaboration ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        // NOTE: Either of these examples produce a conversation
        // whose duration may vary depending on the collaboration dynamics.
        // It is sometimes possible that agreement is never achieved.

        // Explicit collaboration
        await RunCollaborationAsync();

        // Coordinate collaboration as plugin agents (equivalent to previous case - shared thread)
        await RunAsPluginsAsync();
    }

    /// <summary>
    /// Show how two agents are able to collaborate as agents on a single thread.
    /// </summary>
    private static async Task RunCollaborationAsync()
    {
        Console.WriteLine("======== Run:Collaboration ========");
        IAgentThread? thread = null;
        try
        {
            // Create copy-writer agent to generate ideas
            var copyWriter = await CreateCopyWriterAsync();
            // Create art-director agent to review ideas, provide feedback and final approval
            var artDirector = await CreateArtDirectorAsync();

            // Create collaboration thread to which both agents add messages.
            thread = await copyWriter.NewThreadAsync();

            // Add the user message
            var messageUser = await thread.AddUserMessageAsync("concept: maps made out of egg cartons.");
            DisplayMessage(messageUser);

            bool isComplete = false;
            do
            {
                // Initiate copy-writer input
                var agentMessages = await thread.InvokeAsync(copyWriter).ToArrayAsync();
                DisplayMessages(agentMessages, copyWriter);

                // Initiate art-director input
                agentMessages = await thread.InvokeAsync(artDirector).ToArrayAsync();
                DisplayMessages(agentMessages, artDirector);

                // Evaluate if goal is met.
                if (agentMessages.First().Content.Contains("PRINT IT", StringComparison.OrdinalIgnoreCase))
                {
                    isComplete = true;
                }
            }
            while (!isComplete);
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(s_agents.Select(a => a.DeleteAsync()));
        }
    }

    /// <summary>
    /// Show how agents can collaborate as agents using the plug-in model.
    /// </summary>
    /// <remarks>
    /// While this may achieve an equivalent result to <see cref="RunCollaborationAsync"/>,
    /// it is not using shared thread state for agent interaction.
    /// </remarks>
    private static async Task RunAsPluginsAsync()
    {
        Console.WriteLine("======== Run:AsPlugins ========");
        try
        {
            // Create copy-writer agent to generate ideas
            var copyWriter = await CreateCopyWriterAsync();
            // Create art-director agent to review ideas, provide feedback and final approval
            var artDirector = await CreateArtDirectorAsync();

            // Create coordinator agent to oversee collaboration
            var coordinator =
                Track(
                    await new AgentBuilder()
                        .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                        .WithInstructions("Reply the provided concept and have the copy-writer generate an marketing idea (copy).  Then have the art-director reply to the copy-writer with a review of the copy.  Always include the source copy in any message.  Always include the art-director comments when interacting with the copy-writer.  Coordinate the repeated replies between the copy-writer and art-director until the art-director approves the copy.")
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
            await Task.WhenAll(s_agents.Select(a => a.DeleteAsync()));
        }
    }

    private async static Task<IAgent> CreateCopyWriterAsync(IAgent? agent = null)
    {
        return
            Track(
                await new AgentBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.")
                    .WithName("Copywriter")
                    .WithDescription("Copywriter")
                    .WithPlugin(agent?.AsPlugin())
                    .BuildAsync());
    }

    private async static Task<IAgent> CreateArtDirectorAsync()
    {
        return
            Track(
                await new AgentBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to determine is the given copy is acceptable to print, even if it isn't perfect.  If not, provide insight on how to refine suggested copy without example.  Always respond to the most recent message by evaluating and providing critique without example.  Always repeat the copy at the beginning.  If copy is acceptable and meets your criteria, say: PRINT IT.")
                    .WithName("Art Director")
                    .WithDescription("Art Director")
                    .BuildAsync());
    }

    private static void DisplayMessages(IEnumerable<IChatMessage> messages, IAgent? agent = null)
    {
        foreach (var message in messages)
        {
            DisplayMessage(message, agent);
        }
    }

    private static void DisplayMessage(IChatMessage message, IAgent? agent = null)
    {
        Console.WriteLine($"[{message.Id}]");
        if (agent != null)
        {
            Console.WriteLine($"# {message.Role}: ({agent.Name}) {message.Content}");
        }
        else
        {
            Console.WriteLine($"# {message.Role}: {message.Content}");
        }
    }

    private static IAgent Track(IAgent agent)
    {
        s_agents.Add(agent);

        return agent;
    }
}
