// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Showcase hiearchical Open AI Agent interactions using semantic kernel.
/// </summary>
public class Example73_AgentAuthoring : BaseTest
{
    /// <summary>
    /// Specific model is required that supports agents and parallel function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-1106-preview";

    // Track agents for clean-up
    private static readonly List<IAgent> s_agents = new();

    [Fact(Skip = "This test take more than 2 minutes to execute")]
    public async Task RunAgentAsync()
    {
        WriteLine("======== Example73_AgentAuthoring ========");
        try
        {
            // Initialize the agent with tools
            IAgent articleGenerator = await CreateArticleGeneratorAsync();

            // "Stream" messages as they become available
            await foreach (IChatMessage message in articleGenerator.InvokeAsync("Thai food is the best in the world"))
            {
                WriteLine($"[{message.Id}]");
                WriteLine($"# {message.Role}: {message.Content}");
            }
        }
        finally
        {
            await Task.WhenAll(s_agents.Select(a => a.DeleteAsync()));
        }
    }

    [Fact(Skip = "This test take more than 2 minutes to execute")]
    public async Task RunAsPluginAsync()
    {
        WriteLine("======== Example73_AgentAuthoring ========");
        try
        {
            // Initialize the agent with tools
            IAgent articleGenerator = await CreateArticleGeneratorAsync();

            // Invoke as a plugin function
            string response = await articleGenerator.AsPlugin().InvokeAsync("Thai food is the best in the world");

            // Display final result
            WriteLine(response);
        }
        finally
        {
            await Task.WhenAll(s_agents.Select(a => a.DeleteAsync()));
        }
    }

    private static async Task<IAgent> CreateArticleGeneratorAsync()
    {
        // Initialize the outline agent
        var outlineGenerator = await CreateOutlineGeneratorAsync();
        // Initialize the research agent
        var sectionGenerator = await CreateResearchGeneratorAsync();

        // Initialize agent so that it may be automatically deleted.
        return
            Track(
                await new AgentBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("You write concise opinionated articles that are published online.  Use an outline to generate an article with one section of prose for each top-level outline element.  Each section is based on research with a maximum of 120 words.")
                    .WithName("Article Author")
                    .WithDescription("Author an article on a given topic.")
                    .WithPlugin(outlineGenerator.AsPlugin())
                    .WithPlugin(sectionGenerator.AsPlugin())
                    .BuildAsync());
    }

    private static async Task<IAgent> CreateOutlineGeneratorAsync()
    {
        // Initialize agent so that it may be automatically deleted.
        return
            Track(
                await new AgentBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Produce an single-level outline (no child elements) based on the given topic with at most 3 sections.")
                    .WithName("Outline Generator")
                    .WithDescription("Generate an outline.")
                    .BuildAsync());
    }

    private static async Task<IAgent> CreateResearchGeneratorAsync()
    {
        // Initialize agent so that it may be automatically deleted.
        return
            Track(
                await new AgentBuilder()
                    .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                    .WithInstructions("Provide insightful research that supports the given topic based on your knowledge of the outline topic.")
                    .WithName("Researcher")
                    .WithDescription("Author research summary.")
                    .BuildAsync());
    }

    private static IAgent Track(IAgent agent)
    {
        s_agents.Add(agent);

        return agent;
    }

    public Example73_AgentAuthoring(ITestOutputHelper output) : base(output)
    {
    }
}
