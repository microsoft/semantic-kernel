// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="AgentChat"/>.
/// </summary>
public class AgentGroupChatTests
{
    /// <summary>
    /// Verify the default state of <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public void VerifyGroupAgentChatDefaultState()
    {
        AgentGroupChat chat = new();
        Assert.Empty(chat.Agents);
        Assert.NotNull(chat.ExecutionSettings);
        Assert.False(chat.IsComplete);

        chat.IsComplete = true;
        Assert.True(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyGroupAgentChatAgentMembershipAsync()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;
        Agent agent4 = CreateMockAgent().Object;

        AgentGroupChat chat = new(agent1, agent2);
        Assert.Equal(2, chat.Agents.Count);

        chat.Add(agent3);
        Assert.Equal(3, chat.Agents.Count);

        var messages = await chat.InvokeAsync(agent4, isJoining: false).ToArrayAsync();
        Assert.Equal(3, chat.Agents.Count);

        messages = await chat.InvokeAsync(agent4).ToArrayAsync();
        Assert.Equal(4, chat.Agents.Count);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyGroupAgentChatMultiTurnAsync()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;

        AgentGroupChat chat =
            new(agent1, agent2, agent3)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy =
                        {
                            // This test is designed to take 9 turns.
                            MaximumIterations = 9,
                        }
                    },
                IsComplete = true
            };

        await Assert.ThrowsAsync<KernelException>(() => chat.InvokeAsync(CancellationToken.None).ToArrayAsync().AsTask());

        chat.ExecutionSettings.TerminationStrategy.AutomaticReset = true;
        var messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
        Assert.Equal(9, messages.Length);
        Assert.False(chat.IsComplete);

        for (int index = 0; index < messages.Length; ++index) // Clean-up
        {
            switch (index % 3)
            {
                case 0:
                    Assert.Equal(agent1.Name, messages[index].AuthorName);
                    break;
                case 1:
                    Assert.Equal(agent2.Name, messages[index].AuthorName);
                    break;
                case 2:
                    Assert.Equal(agent3.Name, messages[index].AuthorName);
                    break;
            }
        }
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyGroupAgentChatFailedSelectionAsync()
    {
        AgentGroupChat chat = Create3AgentChat();

        chat.ExecutionSettings =
            new()
            {
                // Strategy that will not select an agent.
                SelectionStrategy = new FailedSelectionStrategy(),
                TerminationStrategy =
                {
                    // Remove max-limit in order to isolate the target behavior.
                    MaximumIterations = int.MaxValue
                }
            };

        // Remove max-limit in order to isolate the target behavior.
        chat.ExecutionSettings.TerminationStrategy.MaximumIterations = int.MaxValue;

        await Assert.ThrowsAsync<InvalidOperationException>(() => chat.InvokeAsync().ToArrayAsync().AsTask());
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyGroupAgentChatMultiTurnTerminationAsync()
    {
        AgentGroupChat chat = Create3AgentChat();

        chat.ExecutionSettings =
            new()
            {
                TerminationStrategy =
                    new TestTerminationStrategy(shouldTerminate: true)
                    {
                        // Remove max-limit in order to isolate the target behavior.
                        MaximumIterations = int.MaxValue
                    }
            };

        var messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
        Assert.Single(messages);
        Assert.True(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyGroupAgentChatDiscreteTerminationAsync()
    {
        Agent agent1 = CreateMockAgent().Object;

        AgentGroupChat chat =
            new()
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy =
                            new TestTerminationStrategy(shouldTerminate: true)
                            {
                                // Remove max-limit in order to isolate the target behavior.
                                MaximumIterations = int.MaxValue
                            }
                    }
            };

        var messages = await chat.InvokeAsync(agent1).ToArrayAsync();
        Assert.Single(messages);
        Assert.True(chat.IsComplete);
    }

    private static AgentGroupChat Create3AgentChat()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;

        return new(agent1, agent2, agent3);
    }

    private static Mock<ChatHistoryKernelAgent> CreateMockAgent()
    {
        Mock<ChatHistoryKernelAgent> agent = new();

        ChatMessageContent[] messages = [new ChatMessageContent(AuthorRole.Assistant, "test")];
        agent.Setup(a => a.InvokeAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), It.IsAny<ILogger>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());

        return agent;
    }

    private sealed class TestTerminationStrategy(bool shouldTerminate) : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            return Task.FromResult(shouldTerminate);
        }
    }

    private sealed class FailedSelectionStrategy : SelectionStrategy
    {
        public override Task<Agent> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            throw new InvalidOperationException();
        }
    }
}
