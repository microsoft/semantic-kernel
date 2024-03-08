// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST // Comment line to enable
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Xunit;
using Xunit.Abstractions;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace SemanticKernel.Experimental.Agents.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating runs.
/// </summary>
/// <remarks>
/// Comment out DISABLEHOST definition to enable tests.
/// Not enabled by default.
/// </remarks>
[Trait("Category", "Integration Tests")]
[Trait("Feature", "Agent")]
public sealed class RunHarness
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
    public RunHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyRunLifecycleAsync()
    {
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .WithInstructions("say something funny")
                .WithName("Fred")
                .WithDescription("funny agent")
                .BuildAsync().ConfigureAwait(true);

        var thread = await agent.NewThreadAsync().ConfigureAwait(true);

        await this.ChatAsync(
            thread,
            agent,
            "I was on my way to the store this morning and...",
            "That was great!  Tell me another.").ConfigureAwait(true);
    }

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyRunFromDefinitionAsync()
    {
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .FromTemplatePath("Templates/PoetAgent.yaml")
                .BuildAsync()
                .ConfigureAwait(true);

        var thread = await agent.NewThreadAsync().ConfigureAwait(true);

        await this.ChatAsync(
            thread,
            agent,
            "Eggs are yummy and beautiful geometric gems.",
            "It rains a lot in Seattle.").ConfigureAwait(true);
    }

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyFunctionLifecycleAsync()
    {
        var gamePlugin = KernelPluginFactory.CreateFromType<GuessingGame>();

        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .FromTemplatePath("Templates/GameAgent.yaml")
                .WithPlugin(gamePlugin)
                .BuildAsync()
                .ConfigureAwait(true);

        var thread = await agent.NewThreadAsync().ConfigureAwait(true);

        await this.ChatAsync(
            thread,
            agent,
            "What is the question for the guessing game?",
            "Is it 'RED'?",
            "What is the answer?").ConfigureAwait(true);
    }

    private async Task ChatAsync(IAgentThread thread, IAgent agent, params string[] messages)
    {
        foreach (var message in messages)
        {
            var messageUser = await thread.AddUserMessageAsync(message).ConfigureAwait(true);
            this.LogMessage(messageUser);

            var agentMessages = await thread.InvokeAsync(agent).ToArrayAsync().ConfigureAwait(true);
            this.LogMessages(agentMessages);
        }
    }

    private void LogMessages(IEnumerable<IChatMessage> messages)
    {
        foreach (var message in messages)
        {
            this.LogMessage(message);
        }
    }

    private void LogMessage(IChatMessage message)
    {
        this._output.WriteLine($"# {message.Id}");
        this._output.WriteLine($"# {message.Content}");
        this._output.WriteLine($"# {message.Role}");
        this._output.WriteLine($"# {message.AgentId}");
    }

    private sealed class GuessingGame
    {
        /// <summary>
        /// Get the question
        /// </summary>
        [KernelFunction, Description("Get the guessing game question")]
        public string GetQuestion() => "What color am I thinking of?";

        /// <summary>
        /// Get the answer
        /// </summary>
        [KernelFunction, Description("Get the answer to the guessing game question.")]
        public string GetAnswer() => "Blue";
    }
}
