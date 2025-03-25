// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

/// <summary>
/// Base test class for testing the <see cref="Agent.InvokeAsync(ChatMessageContent, AgentThread?, AgentInvokeOptions?, System.Threading.CancellationToken)"/> method of agents.
/// Each agent type should have its own derived class.
/// </summary>
public abstract class InvokeTests(Func<AgentFixture> createAgentFixture) : IAsyncLifetime
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private AgentFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected AgentFixture Fixture => this._agentFixture;

    [Fact]
    public virtual async Task InvokeReturnsResultAsync()
    {
        var agent = this.Fixture.Agent;
        var asyncResults = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."), this.Fixture.AgentThread);
        var results = await asyncResults.ToListAsync();
        Assert.Single(results);

        var firstResult = results.First();
        Assert.Contains("Paris", firstResult.Message.Content);
        Assert.NotNull(firstResult.Thread);
    }

    [Fact]
    public virtual async Task InvokeWithoutThreadCreatesThreadAsync()
    {
        var agent = this.Fixture.Agent;
        var asyncResults = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."));
        var results = await asyncResults.ToListAsync();
        Assert.Single(results);

        var firstResult = results.First();
        Assert.Contains("Paris", firstResult.Message.Content);
        Assert.NotNull(firstResult.Thread);

        await this.Fixture.DeleteThread(firstResult.Thread);
    }

    [Fact]
    public virtual async Task ConversationMaintainsHistoryAsync()
    {
        var q1 = "What is the capital of France.";
        var q2 = "What is the capital of Austria.";

        var agent = this.Fixture.Agent;
        var asyncResults1 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, q1), this.Fixture.AgentThread);
        var result1 = await asyncResults1.FirstAsync();
        var asyncResults2 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, q2), result1.Thread);
        var result2 = await asyncResults2.FirstAsync();

        Assert.Contains("Paris", result1.Message.Content);
        Assert.Contains("Austria", result2.Message.Content);

        var chatHistory = await this.Fixture.GetChatHistory();

        Assert.Equal(4, chatHistory.Count);
        Assert.Equal(2, chatHistory.Count(x => x.Role == AuthorRole.User));
        Assert.Equal(2, chatHistory.Count(x => x.Role == AuthorRole.Assistant));
        Assert.Equal(q1, chatHistory[0].Content);
        Assert.Equal(q2, chatHistory[2].Content);
        Assert.Contains("Paris", chatHistory[1].Content);
        Assert.Contains("Vienna", chatHistory[3].Content);
    }

    public Task InitializeAsync()
    {
        this._agentFixture = createAgentFixture();
        return this._agentFixture.InitializeAsync();
    }

    public Task DisposeAsync()
    {
        return this._agentFixture.DisposeAsync();
    }
}
