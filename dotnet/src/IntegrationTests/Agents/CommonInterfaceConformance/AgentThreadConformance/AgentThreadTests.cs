// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public abstract class AgentThreadTests(Func<AgentFixture> createAgentFixture) : IAsyncLifetime
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private AgentFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected AgentFixture Fixture => this._agentFixture;

    [Fact]
    public async Task DeletingThreadTwiceDoesNotThrowAsync()
    {
        await this.Fixture.AgentThread.CreateAsync();

        await this.Fixture.AgentThread.DeleteAsync();
        await this.Fixture.AgentThread.DeleteAsync();
    }

    [Fact]
    public async Task UsingThreadAfterDeleteThrowsAsync()
    {
        await this.Fixture.AgentThread.CreateAsync();
        await this.Fixture.AgentThread.DeleteAsync();

        await Assert.ThrowsAsync<InvalidOperationException>(async () => await this.Fixture.AgentThread.CreateAsync());
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await this.Fixture.AgentThread.OnNewMessageAsync(new ChatMessageContent()));
    }

    [Fact]
    public async Task DeleteThreadBeforeCreateThrowsAsync()
    {
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await this.Fixture.AgentThread.DeleteAsync());
    }

    [Fact]
    public async Task UsingThreadbeforeCreateCreatesAsync()
    {
        await this.Fixture.AgentThread.OnNewMessageAsync(new ChatMessageContent());
        Assert.NotNull(this.Fixture.AgentThread.Id);
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
