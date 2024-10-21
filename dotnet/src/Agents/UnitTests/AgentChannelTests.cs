// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentChannel"/>.
/// </summary>
public class AgentChannelTests
{
    /// <summary>
    /// Verify a <see cref="AgentChannel{TAgent}"/> throws if passed
    /// an agent type that does not match declared agent type (TAgent).
    /// </summary>
    [Fact]
    public async Task VerifyAgentChannelUpcastAsync()
    {
        // Arrange
        TestChannel channel = new();
        MockChannel channel = new();
        // Assert
        Assert.Equal(0, channel.InvokeCount);

        // Act
        var messages = channel.InvokeAgentAsync(new MockAgent()).ToArrayAsync();
        var messages = await channel.InvokeAgentAsync(new MockAgent()).ToArrayAsync();
        // Assert
        Assert.Equal(1, channel.InvokeCount);

        // Act
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAgentAsync(new NextAgent()).ToArrayAsync().AsTask());
        // Assert
        Assert.Equal(1, channel.InvokeCount);
    }

    /// <summary>
    /// Not using mock as the goal here is to provide entrypoint to protected method.
    /// </summary>
    private sealed class TestChannel : AgentChannel<MockAgent>
    {
        public int InvokeCount { get; private set; }

        public IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAgentAsync(Agent agent, CancellationToken cancellationToken = default)
            => base.InvokeAsync(agent, cancellationToken);

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        protected internal override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(MockAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
        {
            this.InvokeCount++;

            yield break;
        }

        protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override string Serialize()
        {
            throw new NotImplementedException();
        }
    }

    private sealed class NextAgent : TestAgent;

        protected internal override Task ResetAsync(CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class NextAgent : MockAgent;
        Mock<Agent> mockAgent = new();
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAgentAsync(mockAgent.Object).ToArrayAsync().AsTask());
        // Assert
        Assert.Equal(1, channel.InvokeCount);
    }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
