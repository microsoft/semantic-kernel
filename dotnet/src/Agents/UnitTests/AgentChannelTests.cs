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
        MockChannel channel = new();
        // Assert
        Assert.Equal(0, channel.InvokeCount);

        // Act
        var messages = await channel.InvokeAgentAsync(new MockAgent()).ToArrayAsync();
        // Assert
        Assert.Equal(1, channel.InvokeCount);

        // Act
        Mock<Agent> mockAgent = new();
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAgentAsync(mockAgent.Object).ToArrayAsync().AsTask());
        // Assert
        Assert.Equal(1, channel.InvokeCount);
    }
}
