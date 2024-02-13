// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Showcase complex Open AI Agent collaboration using semantic kernel.
/// </summary>
public class Example72_AgentCollaboration : BaseTest
{
    /// <summary>
    /// Specific model is required that supports agents and function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-turbo-preview";

    /// <summary>
    /// Set this to 'true' to target OpenAI instead of Azure OpenAI.
    /// </summary>
    private const bool UseOpenAI = false;

    // Track agents for clean-up
    private static readonly List<IAgent> s_agents = new();

    /// <summary>
    /// Show how two agents are able to collaborate as agents on a single thread.
    /// </summary>
    [Fact(Skip = "This test take more than 5 minutes to execute")]
    public async Task RunCollaborationAsync()
    {
        WriteLine($"======== Example72:Collaboration:{(UseOpenAI ? "OpenAI" : "AzureAI")} ========");

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
    [Fact(Skip = "This test take more than 2 minutes to execute")]
    public async Task RunAsPluginsAsync()
    {
        WriteLine($"======== Example72:AsPlugins:{(UseOpenAI ? "OpenAI" : "AzureAI")} ========");

        try
        {
            // Create copy-writer agent to generate ideas
            var copyWriter = await CreateCopyWriterAsync();
            // Create art-director agent to review ideas, provide feedback and final approval
            var artDirector = await CreateArtDirectorAsync();

            // Create coordinator agent to oversee collaboration
            var coordinator =
                Track(
                    await CreateAgentBuilder()
                        .WithInstructions("Reply the provided concept and have the copy-writer generate an marketing idea (copy).  Then have the art-director reply to the copy-writer with a review of the copy.  Always include the source copy in any message.  Always include the art-director comments when interacting with the copy-writer.  Coordinate the repeated replies between the copy-writer and art-director until the art-director approves the copy.")
                        .WithPlugin(copyWriter.AsPlugin())
                        .WithPlugin(artDirector.AsPlugin())
                        .BuildAsync());

            // Invoke as a plugin function
            var response = await coordinator.AsPlugin().InvokeAsync("concept: maps made out of egg cartons.");

            // Display final result
            WriteLine(response);
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(s_agents.Select(a => a.DeleteAsync()));
        }
    }

    private static async Task<IAgent> CreateCopyWriterAsync(IAgent? agent = null)
    {
        return
            Track(
                await CreateAgentBuilder()
                    .WithInstructions("You are a copywriter with ten years of experience and are known for b/threadsrevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.")
                    .WithName("Copywriter")
                    .WithDescription("Copywriter")
                    .WithPlugin(agent?.AsPlugin())
                    .BuildAsync());
    }

    private async static Task<IAgent> CreateArtDirectorAsync()
    {
        return
            Track(
                await CreateAgentBuilder()
                    .WithInstructions("You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to determine is the given copy is acceptable to print, even if it isn't perfect.  If not, provide insight on how to refine suggested copy without example.  Always respond to the most recent message by evaluating and providing critique without example.  Always repeat the copy at the beginning.  If copy is acceptable and meets your criteria, say: PRINT IT.")
                    .WithName("Art Director")
                    .WithDescription("Art Director")
                    .BuildAsync());
    }

    private static AgentBuilder CreateAgentBuilder()
    {
        var builder = new AgentBuilder();

        return
            UseOpenAI ?
                builder.WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey) :
                builder.WithAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.DeploymentName, TestConfiguration.AzureOpenAI.ApiKey);
    }

    private void DisplayMessages(IEnumerable<IChatMessage> messages, IAgent? agent = null)
    {
        foreach (var message in messages)
        {
            DisplayMessage(message, agent);
        }
    }

    private void DisplayMessage(IChatMessage message, IAgent? agent = null)
    {
        WriteLine($"[{message.Id}]");
        if (agent != null)
        {
            WriteLine($"# {message.Role}: ({agent.Name}) {message.Content}");
        }
        else
        {
            WriteLine($"# {message.Role}: {message.Content}");
        }
    }

    private static IAgent Track(IAgent agent)
    {
        s_agents.Add(agent);

        return agent;
    }

    public Example72_AgentCollaboration(ITestOutputHelper output) : base(output)
    {
    }
}
