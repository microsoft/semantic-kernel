// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="SequentialSelectionStrategy"/>.
/// </summary>
public class SequentialSelectionStrategyTests
{
    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> provides agents in expected order.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyTurnsAsync()
    {
        // Arrange
        MockAgent agent1 = new();
        MockAgent agent2 = new();

        Agent[] agents = [agent1, agent2];
        SequentialSelectionStrategy strategy = new();

        // Act and Assert
        await VerifyNextAgent(agent1);
        await VerifyNextAgent(agent2);
        await VerifyNextAgent(agent1);
        await VerifyNextAgent(agent2);
        await VerifyNextAgent(agent1);

        // Arrange
        strategy.Reset();

        // Act and Assert
        await VerifyNextAgent(agent1);

        // Arrange: Verify index does not exceed current bounds.
        agents = [agent1];

        // Act and Assert
        await VerifyNextAgent(agent1);

        async Task VerifyNextAgent(Agent agent1)
        {
            // Act
            Agent? nextAgent = await strategy.NextAsync(agents, []);

            // Assert
            Assert.NotNull(nextAgent);
            Assert.Equal(agent1.Id, nextAgent.Id);
        }
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> behavior with no agents.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyEmptyAsync()
    {
        // Arrange
        SequentialSelectionStrategy strategy = new();

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([], []));
    }
}
