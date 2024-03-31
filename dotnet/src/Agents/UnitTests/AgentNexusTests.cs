// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Threading;
using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;
using Microsoft.SemanticKernel.ChatCompletion;
using System.Runtime.CompilerServices;
using System.Linq;

namespace SemanticKernel.Agents.UnitTests;

public class AgentNexusTests
{
    [Fact]
    public async Task VerifyAgentNexusLifecycleAsync()
    {
        TestNexus nexus = new();
        var messages = await nexus.GetHistoryAsync().ToArrayAsync();
        Assert.Empty(messages);
        messages = await nexus.GetHistoryAsync(nexus.Agent).ToArrayAsync();
        Assert.Empty(messages);

        nexus.AppendHistory([new ChatMessageContent(AuthorRole.User, "More")]);
        nexus.AppendHistory([new ChatMessageContent(AuthorRole.User, "And then some")]);

        //await Task.Delay(1000);

        messages = await nexus.GetHistoryAsync().ToArrayAsync();
        Assert.NotEmpty(messages);
        Assert.Equal(2, messages.Length);
        messages = await nexus.GetHistoryAsync(nexus.Agent).ToArrayAsync();
        Assert.Empty(messages); // Agent hasn't joined

        messages = await nexus.InvokeAsync("hi").ToArrayAsync();
        Assert.Equal(1, nexus.Agent.InvokeCount);

        messages = await nexus.InvokeAsync().ToArrayAsync();
        Assert.Equal(2, nexus.Agent.InvokeCount);

        messages = await nexus.GetHistoryAsync().ToArrayAsync();
        Assert.NotEmpty(messages);
        Assert.Equal(5, messages.Length);
        messages = await nexus.GetHistoryAsync(nexus.Agent).ToArrayAsync();
        Assert.NotEmpty(messages); // Agent joined
        Assert.Equal(5, messages.Length);
    }

    private sealed class TestNexus : AgentNexus
    {
        public TestAgent Agent { get; } = new TestAgent();

        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            string? input = null,
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, CreateUserMessage(input), cancellationToken);
    }

    private class TestAgent()
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
