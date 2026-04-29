// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.SemanticKernelAIAgentConformance;

public abstract class SemanticKernelAIAgentTests(Func<AgentFixture> createAgentFixture) : IAsyncLifetime
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private AgentFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected AgentFixture Fixture => this._agentFixture;

    [Fact]
    public virtual async Task ConvertAndRunAgentAsync()
    {
        var aiagent = this.Fixture.AIAgent;
        var session = await aiagent.CreateSessionAsync();

        var result = await aiagent.RunAsync("What is the capital of France?", session);
        Assert.Contains("Paris", result.Text, StringComparison.OrdinalIgnoreCase);

        var serialisedSessionJsonElement = await aiagent.SerializeSessionAsync(session);

        var deserializedSession = await aiagent.DeserializeSessionAsync(serialisedSessionJsonElement);

        var secondResult = await aiagent.RunAsync("And Austria?", deserializedSession);
        Assert.Contains("Vienna", secondResult.Text, StringComparison.OrdinalIgnoreCase);
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
