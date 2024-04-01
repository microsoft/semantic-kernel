// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentNexus"/>.
/// </summary>
public class AgentNexusTests
{
    /// <summary>
    /// Verify behavior of <see cref="AgentNexus"/> over the course of agent interactions.
    /// </summary>
    [Fact]
    public async Task VerifyAgentNexusLifecycleAsync()
    {
        // Create nexus
        TestNexus nexus = new();

        // Verify initial state
        await this.VerifyHistoryAsync(expectedCount: 0, nexus.GetHistoryAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, nexus.GetHistoryAsync(nexus.Agent)); // Agent history

        // Inject history
        nexus.AppendHistory([new ChatMessageContent(AuthorRole.User, "More")]);
        nexus.AppendHistory([new ChatMessageContent(AuthorRole.User, "And then some")]);

        // Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 2, nexus.GetHistoryAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, nexus.GetHistoryAsync(nexus.Agent)); // Agent hasn't joined

        // Invoke with input & verify (agent joins chat)
        await nexus.InvokeAsync("hi").ToArrayAsync();
        Assert.Equal(1, nexus.Agent.InvokeCount);

        // Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 4, nexus.GetHistoryAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 4, nexus.GetHistoryAsync(nexus.Agent)); // Agent history

        // Invoke without input & verify
        await nexus.InvokeAsync().ToArrayAsync();
        Assert.Equal(2, nexus.Agent.InvokeCount);

        // Verify final history
        await this.VerifyHistoryAsync(expectedCount: 5, nexus.GetHistoryAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 5, nexus.GetHistoryAsync(nexus.Agent)); // Agent history
    }

    private async Task VerifyHistoryAsync(int expectedCount, IAsyncEnumerable<ChatMessageContent> history)
    {
        if (expectedCount == 0)
        {
            Assert.Empty(history);
        }
        else
        {
            Assert.NotEmpty(history);
            Assert.Equal(expectedCount, await history.CountAsync());
        }
    }

    private sealed class TestNexus : AgentNexus
    {
        public TestAgent Agent { get; } = new TestAgent();

        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            string? input = null,
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, CreateUserMessage(input), cancellationToken);
    }

    private sealed class TestAgent()
        : LocalKernelAgent(Kernel.CreateBuilder().Build())
    {
        public override string? Description { get; } = null;

        public override string Id => Guid.NewGuid().ToString();

        public override string? Name { get; } = null;

        public int InvokeCount { get; private set; }

        public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(IEnumerable<ChatMessageContent> history, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.Delay(0, cancellationToken);

            this.InvokeCount += 1;

            yield return new ChatMessageContent(AuthorRole.Assistant, "sup");
        }
    }
}
