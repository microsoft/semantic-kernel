// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST // Comment line to enable
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Agents.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating agents.
/// </summary>
/// <remarks>
/// Comment out DISABLEHOST definition to enable tests.
/// Not enabled by default.
/// </remarks>
[Trait("Category", "Integration Tests")]
[Trait("Feature", "Agent")]
public sealed class AgentHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    /// <summary>
    /// Test constructor.
    /// </summary>
    public AgentHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Verify creation and retrieval of agent.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAgentLifecycleAsync()
    {
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .WithInstructions("say something funny")
                .WithName("Fred")
                .WithDescription("test agent")
                .BuildAsync().ConfigureAwait(true);

        this.DumpAgent(agent);

        var copy =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .GetAsync(agentId: agent.Id).ConfigureAwait(true);

        this.DumpAgent(copy);
    }

    /// <summary>
    /// Verify creation and retrieval of agent.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAgentDefinitionAsync()
    {
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .FromTemplatePath("Templates/PoetAgent.yaml")
                .BuildAsync()
                .ConfigureAwait(true);

        this.DumpAgent(agent);

        var copy =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .GetAsync(agentId: agent.Id).ConfigureAwait(true);

        this.DumpAgent(copy);
    }

    /// <summary>
    /// Verify creation and retrieval of agent.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAgentListAsync()
    {
        var context = new OpenAIRestContext(AgentBuilder.OpenAIBaseUrl, TestConfig.OpenAIApiKey);
        var agents = await context.ListAssistantModelsAsync().ConfigureAwait(true);
        foreach (var agent in agents)
        {
            this.DumpAgent(agent);
        }
    }

    /// <summary>
    /// Verify creation and retrieval of agent.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAgentDeleteAsync()
    {
        var names =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "Fred",
                "Barney",
                "DeleteMe",
                "Poet",
                "Math Tutor",
            };

        var context = new OpenAIRestContext(AgentBuilder.OpenAIBaseUrl, TestConfig.OpenAIApiKey);
        var agents = await context.ListAssistantModelsAsync().ConfigureAwait(true);
        foreach (var agent in agents)
        {
            if (!string.IsNullOrWhiteSpace(agent.Name) && names.Contains(agent.Name))
            {
                this._output.WriteLine($"Removing: {agent.Name} - {agent.Id}");
                await context.DeleteAssistantModelAsync(agent.Id).ConfigureAwait(true);
            }
        }
    }

    private void DumpAgent(AssistantModel agent)
    {
        this._output.WriteLine($"# {agent.Id}");
        this._output.WriteLine($"# {agent.Model}");
        this._output.WriteLine($"# {agent.Instructions}");
        this._output.WriteLine($"# {agent.Name}");
        this._output.WriteLine($"# {agent.Description}{Environment.NewLine}");
    }

    private void DumpAgent(IAgent agent)
    {
        this._output.WriteLine($"# {agent.Id}");
        this._output.WriteLine($"# {agent.Model}");
        this._output.WriteLine($"# {agent.Instructions}");
        this._output.WriteLine($"# {agent.Name}");
        this._output.WriteLine($"# {agent.Description}{Environment.NewLine}");
    }
}
