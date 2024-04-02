// Copyright (c) Microsoft. All rights reserved.
using System;
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
        Mock<Agent> agent1 = CreateMockAgent();
        Mock<Agent> agent2 = CreateMockAgent();

        Agent[] agents = new[] { agent1.Object, agent2.Object };
        SequentialSelectionStrategy strategy = new();

        await VerifyNextAgent(agent1.Object);
        await VerifyNextAgent(agent2.Object);
        await VerifyNextAgent(agent1.Object);
        await VerifyNextAgent(agent2.Object);
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

        static Mock<Agent> CreateMockAgent()
        {
            Mock<Agent> agent = new();

            string id = Guid.NewGuid().ToString();
            agent.SetupGet(a => a.Id).Returns(id);

            return agent;
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
}
