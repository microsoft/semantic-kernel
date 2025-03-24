// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public abstract class AgentThreadTests(Func<AgentFixture> createAgentFixture) : IAsyncLifetime
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private AgentFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected AgentFixture Fixture => this._agentFixture;

    [Fact]
    public virtual async Task DeletingThreadTwiceDoesNotThrowAsync()
    {
        await this.Fixture.CreatedAgentThread.DeleteAsync();
        await this.Fixture.CreatedAgentThread.DeleteAsync();
    }

    [Fact]
    public virtual async Task UsingThreadAfterDeleteThrowsAsync()
    {
        await this.Fixture.CreatedAgentThread.DeleteAsync();

        await Assert.ThrowsAsync<InvalidOperationException>(async () => await InvokeInternalOnNewMessage(this.Fixture.CreatedAgentThread, new ChatMessageContent(AuthorRole.User, "Hi")));
    }

    [Fact]
    public virtual async Task DeleteThreadBeforeCreateThrowsAsync()
    {
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await this.Fixture.AgentThread.DeleteAsync());
    }

    [Fact]
    public virtual async Task UsingThreadBeforeCreateCreatesAsync()
    {
        await InvokeInternalOnNewMessage(this.Fixture.AgentThread, new ChatMessageContent(AuthorRole.User, "Hi"));
        Assert.NotNull(this.Fixture.AgentThread.Id);
    }

    [Fact]
    public virtual async Task DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        await Assert.ThrowsAsync<AgentThreadOperationException>(async () => await this.Fixture.CreatedServiceFailingAgentThread.DeleteAsync());
    }

    [Fact]
    public virtual async Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        await Assert.ThrowsAsync<AgentThreadOperationException>(
            async () => await InvokeInternalOnNewMessage(this.Fixture.CreatedServiceFailingAgentThread, new ChatMessageContent(AuthorRole.User, "Hi")));
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

    private static Task InvokeInternalOnNewMessage(AgentThread thread, ChatMessageContent message)
    {
        // User reflection to invoke the internal method.
        var method = thread.GetType().GetMethod("OnNewMessageAsync", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        if (method == null)
        {
            throw new InvalidOperationException("Method not found");
        }

        var task = (Task)method.Invoke(thread, new object[] { message, CancellationToken.None })!;
        return task;
    }
}
