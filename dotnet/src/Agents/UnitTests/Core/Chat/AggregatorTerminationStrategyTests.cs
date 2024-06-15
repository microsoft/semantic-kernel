// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="AggregatorTerminationStrategy"/>.
/// </summary>
public class AggregatorTerminationStrategyTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyAggregateTerminationStrategyInitialState()
    {
        AggregatorTerminationStrategy strategy = new();
        Assert.Equal(AggregateTerminationCondition.All, strategy.Condition);
    }

    /// <summary>
    /// Verify evaluation of AggregateTerminationCondition.Any.
    /// </summary>
    [Fact]
    public async Task VerifyAggregateTerminationStrategyAnyAsync()
    {
        TerminationStrategy strategyMockTrue = new MockTerminationStrategy(terminationResult: true);
        TerminationStrategy strategyMockFalse = new MockTerminationStrategy(terminationResult: false);

        Mock<Agent> agentMock = new();

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue, strategyMockFalse)
            {
                Condition = AggregateTerminationCondition.Any,
            });

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockFalse, strategyMockFalse)
            {
                Condition = AggregateTerminationCondition.Any,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue, strategyMockTrue)
            {
                Condition = AggregateTerminationCondition.Any,
            });
    }

    /// <summary>
    /// Verify evaluation of AggregateTerminationCondition.All.
    /// </summary>
    [Fact]
    public async Task VerifyAggregateTerminationStrategyAllAsync()
    {
        TerminationStrategy strategyMockTrue = new MockTerminationStrategy(terminationResult: true);
        TerminationStrategy strategyMockFalse = new MockTerminationStrategy(terminationResult: false);

        Mock<Agent> agentMock = new();

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockTrue, strategyMockFalse)
            {
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockFalse, strategyMockFalse)
            {
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue, strategyMockTrue)
            {
                Condition = AggregateTerminationCondition.All,
            });
    }

    /// <summary>
    /// Verify evaluation of agent scope evaluation.
    /// </summary>
    [Fact]
    public async Task VerifyAggregateTerminationStrategyAgentAsync()
    {
        TerminationStrategy strategyMockTrue = new MockTerminationStrategy(terminationResult: true);
        TerminationStrategy strategyMockFalse = new MockTerminationStrategy(terminationResult: false);

        Mock<Agent> agentMockA = new();
        Mock<Agent> agentMockB = new();

        await VerifyResultAsync(
            expectedResult: false,
            agentMockB.Object,
            new(strategyMockTrue, strategyMockTrue)
            {
                Agents = [agentMockA.Object],
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMockB.Object,
            new(strategyMockTrue, strategyMockTrue)
            {
                Agents = [agentMockB.Object],
                Condition = AggregateTerminationCondition.All,
            });
    }

    private static async Task VerifyResultAsync(bool expectedResult, Agent agent, AggregatorTerminationStrategy strategyRoot)
    {
        var result = await strategyRoot.ShouldTerminateAsync(agent, []);
        Assert.Equal(expectedResult, result);
    }

    /// <summary>
    /// Less side-effects when mocking protected method.
    /// </summary>
    private sealed class MockTerminationStrategy(bool terminationResult) : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(terminationResult);
    }
}
