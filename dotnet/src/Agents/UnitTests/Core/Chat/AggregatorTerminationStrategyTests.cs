// Copyright (c) Microsoft. All rights reserved.
using System;
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
        Mock<TerminationStrategy> strategyMockTrue = CreateMockStrategy(evaluate: true);
        Mock<TerminationStrategy> strategyMockFalse = CreateMockStrategy(evaluate: false);

        Mock<Agent> agentMock = new();

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue.Object, strategyMockFalse.Object)
            {
                Condition = AggregateTerminationCondition.Any,
            });

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockFalse.Object, strategyMockFalse.Object)
            {
                Condition = AggregateTerminationCondition.Any,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue.Object, strategyMockTrue.Object)
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
        Mock<TerminationStrategy> strategyMockTrue = CreateMockStrategy(evaluate: true);
        Mock<TerminationStrategy> strategyMockFalse = CreateMockStrategy(evaluate: false);

        Mock<Agent> agentMock = new();

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockTrue.Object, strategyMockFalse.Object)
            {
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: false,
            agentMock.Object,
            new(strategyMockFalse.Object, strategyMockFalse.Object)
            {
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMock.Object,
            new(strategyMockTrue.Object, strategyMockTrue.Object)
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
        Mock<TerminationStrategy> strategyMockTrue = CreateMockStrategy(evaluate: true);
        Mock<TerminationStrategy> strategyMockFalse = CreateMockStrategy(evaluate: false);

        Mock<Agent> agentMockA = new();
        Mock<Agent> agentMockB = new();

        await VerifyResultAsync(
            expectedResult: false,
            agentMockB.Object,
            new(strategyMockTrue.Object, strategyMockTrue.Object)
            {
                Agents = new[] { agentMockA.Object },
                Condition = AggregateTerminationCondition.All,
            });

        await VerifyResultAsync(
            expectedResult: true,
            agentMockB.Object,
            new(strategyMockTrue.Object, strategyMockTrue.Object)
            {
                Agents = new[] { agentMockB.Object },
                Condition = AggregateTerminationCondition.All,
            });
    }

    private static Mock<TerminationStrategy> CreateMockStrategy(bool evaluate)
    {
        Mock<TerminationStrategy> strategyMock = new();

        strategyMock
            .Setup(s => s.ShouldTerminateAsync(It.IsAny<Agent>(), It.IsAny<IReadOnlyList<ChatMessageContent>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.FromResult(evaluate));

        return strategyMock;
    }

    private static async Task VerifyResultAsync(bool expectedResult, Agent agent, AggregatorTerminationStrategy strategyRoot)
    {
        var result = await strategyRoot.ShouldTerminateAsync(agent, Array.Empty<ChatMessageContent>());
        Assert.Equal(expectedResult, result);
    }
}
