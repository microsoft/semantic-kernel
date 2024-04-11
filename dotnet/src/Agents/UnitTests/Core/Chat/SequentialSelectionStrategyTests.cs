// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Reflection;
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

        Agent[] agents = new[] { agent1.Object, agent2.Object };
        SequentialSelectionStrategy strategy = new();

        await VerifyNextAgent(agent1.Object);
        await VerifyNextAgent(agent2.Object);
        await VerifyNextAgent(agent1.Object);
        await VerifyNextAgent(agent2.Object);
        await VerifyNextAgent(agent1.Object);

        strategy.Reset();
        await VerifyNextAgent(agent1.Object);

        // Verify index does not exceed current bounds.
        agents = new[] { agent1.Object };
        await VerifyNextAgent(agent1.Object);

        async Task VerifyNextAgent(Agent agent1)
        {
            Agent? nextAgent = await strategy.NextAsync(agents, Array.Empty<ChatMessageContent>());
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
        SequentialSelectionStrategy strategy = new();
        Agent? nextAgent = await strategy.NextAsync(Array.Empty<Agent>(), Array.Empty<ChatMessageContent>());
        Assert.Null(nextAgent);
    }

    /// <summary>
    /// Verify <see cref="SequentialSelectionStrategy"/> maintaines order consistency
    /// for int.MaxValue + 1 number of turns.
    /// </summary>
    [Fact]
    public async Task VerifySequentialSelectionStrategyOverflowAsync()
    {
        Mock<Agent> agent1 = new();
        Mock<Agent> agent2 = new();
        Mock<Agent> agent3 = new();

        Agent[] agents = new[] { agent1.Object, agent2.Object, agent3.Object };
        SequentialSelectionStrategy strategy = new();

        typeof(SequentialSelectionStrategy)
            .GetField("_index", BindingFlags.NonPublic | BindingFlags.SetField | BindingFlags.Instance)!
            .SetValue(strategy, int.MaxValue);

        var nextAgent = await strategy.NextAsync(agents, Array.Empty<ChatMessageContent>());
        Assert.NotNull(nextAgent);
        Assert.Equal(agent2.Object.Id, nextAgent.Id);
    }
}
