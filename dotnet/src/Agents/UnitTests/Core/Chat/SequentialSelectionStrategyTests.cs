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
        await VerifyNextAgentAsync(agent1, agents, strategy);
        await VerifyNextAgentAsync(agent2, agents, strategy);
        await VerifyNextAgentAsync(agent1, agents, strategy);
        await VerifyNextAgentAsync(agent2, agents, strategy);
        await VerifyNextAgentAsync(agent1, agents, strategy);

        // Arrange
        strategy.Reset();
        await VerifyNextAgentAsync(agent1, agents, strategy);

        // Verify index does not exceed current bounds.
        agents = [agent1];
        await VerifyNextAgentAsync(agent1, agents, strategy);
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> provides agents in expected order.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyInitialLastAgentAsync()
    {
        MockAgent agent1 = new();
        MockAgent agent2 = new();

        Agent[] agents = [agent1, agent2];
        SequentialSelectionStrategy strategy =
            new()
            {
                InitialAgent = agent2
            };

        await VerifyNextAgentAsync(agent2, agents, strategy);
        await VerifyNextAgentAsync(agent1, agents, strategy);
        await VerifyNextAgentAsync(agent2, agents, strategy);
        await VerifyNextAgentAsync(agent1, agents, strategy);
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> provides agents in expected order.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyInitialFirstAgentAsync()
    {
        MockAgent agent1 = new();
        MockAgent agent2 = new();

        Agent[] agents = [agent1, agent2];
        SequentialSelectionStrategy strategy =
            new()
            {
                InitialAgent = agent1
            };

        await VerifyNextAgentAsync(agent1, agents, strategy);
        await VerifyNextAgentAsync(agent2, agents, strategy);
        await VerifyNextAgentAsync(agent1, agents, strategy);
        await VerifyNextAgentAsync(agent2, agents, strategy);
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

    private static async Task VerifyNextAgentAsync(Agent expectedAgent, Agent[] agents, SequentialSelectionStrategy strategy)
    {
        // Act
        Agent? nextAgent = await strategy.NextAsync(agents, []);
        // Assert
        Assert.NotNull(nextAgent);
        Assert.Equal(expectedAgent.Id, nextAgent.Id);
    }
}
