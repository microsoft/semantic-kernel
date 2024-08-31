// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
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
        Mock<Agent> agent1 = new();
        Mock<Agent> agent2 = new();

        Agent[] agents = [agent1.Object, agent2.Object];
        SequentialSelectionStrategy strategy = new();

        await VerifyNextAgentAsync(agent1.Object, agents, strategy);
        await VerifyNextAgentAsync(agent2.Object, agents, strategy);
        await VerifyNextAgentAsync(agent1.Object, agents, strategy);
        await VerifyNextAgentAsync(agent2.Object, agents, strategy);
        await VerifyNextAgentAsync(agent1.Object, agents, strategy);

        strategy.Reset();
        await VerifyNextAgentAsync(agent1.Object, agents, strategy);

        // Verify index does not exceed current bounds.
        agents = [agent1.Object];
        await VerifyNextAgentAsync(agent1.Object, agents, strategy);
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> provides agents in expected order.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyInitialAgentAsync()
    {
        Mock<Agent> agent1 = new();
        Mock<Agent> agent2 = new();

        Agent[] agents = [agent1.Object, agent2.Object];
        SequentialSelectionStrategy strategy =
            new()
            {
                InitialAgent = agent2.Object
            };

        await VerifyNextAgentAsync(agent2.Object, agents, strategy);
        await VerifyNextAgentAsync(agent1.Object, agents, strategy);
    }

    private static async Task VerifyNextAgentAsync(Agent expectedAgent, Agent[] agents, SequentialSelectionStrategy strategy)
    {
        Agent? nextAgent = await strategy.NextAsync(agents, []);
        Assert.NotNull(nextAgent);
        Assert.Equal(expectedAgent.Id, nextAgent.Id);
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> behavior with no agents.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyEmptyAsync()
    {
        SequentialSelectionStrategy strategy = new();
        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([], []));
    }
}
