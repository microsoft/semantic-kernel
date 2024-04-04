// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
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
public class AgentChatTests
{
    /// <summary>
    /// Verify the default state of <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public void VerifyAgentChatDefaultState()
    {
        AgentChat chat = new();
        Assert.Empty(chat.Agents);
        Assert.Null(chat.ExecutionSettings);
        Assert.False(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatAgentMembershipAsync()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;
        Agent agent4 = CreateMockAgent().Object;

        AgentChat chat = new(agent1, agent2);
        Assert.Equal(2, chat.Agents.Count);

        chat.AddAgent(agent3);
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
    public async Task VerifyAgentChatMultiTurnAsync()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;

        AgentChat chat =
            new(agent1, agent2, agent3)
            {
                ExecutionSettings =
                    new()
                    {
                        SelectionStrategy = new SequentialSelectionStrategy(),
                        MaximumIterations = 9,
                    }
            };

        chat.IsComplete = true;
        var messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
        Assert.Empty(messages);

        chat.IsComplete = false;
        messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
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
    public async Task VerifyAgentChatNullSettingsAsync()
    {
        AgentChat chat = Create3AgentChat();

        chat.ExecutionSettings = null;

        var messages = await chat.InvokeAsync().ToArrayAsync();
        Assert.Empty(messages);
        Assert.False(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatNoStrategyAsync()
    {
        AgentChat chat = Create3AgentChat();

        chat.ExecutionSettings =
            new()
            {
                MaximumIterations = int.MaxValue,
            };

        var messages = await chat.InvokeAsync().ToArrayAsync();
        Assert.Empty(messages);
        Assert.False(chat.IsComplete);

        Agent agent4 = CreateMockAgent().Object;
        messages = await chat.InvokeAsync(agent4).ToArrayAsync();
        Assert.Single(messages);
        Assert.False(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatNullSelectionAsync()
    {
        AgentChat chat = Create3AgentChat();

        chat.ExecutionSettings =
            new()
            {
                SelectionStrategy = (_, _, _) => Task.FromResult<Agent?>(null),
                MaximumIterations = int.MaxValue,
            };

        var messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
        Assert.Empty(messages);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatMultiTurnTerminationAsync()
    {
        AgentChat chat = Create3AgentChat();

        chat.ExecutionSettings =
            new()
            {
                SelectionStrategy = new SequentialSelectionStrategy(),
                TerminationStrategy = (_, _, _) => Task.FromResult(true),
                MaximumIterations = int.MaxValue,
            };

        var messages = await chat.InvokeAsync(CancellationToken.None).ToArrayAsync();
        Assert.Single(messages);
        Assert.True(chat.IsComplete);
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatDiscreteTerminationAsync()
    {
        Agent agent1 = CreateMockAgent().Object;

        AgentChat chat =
            new()
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy = (_, _, _) => Task.FromResult(true),
                        MaximumIterations = int.MaxValue,
                    }
            };

        var messages = await chat.InvokeAsync(agent1).ToArrayAsync();
        Assert.Single(messages);
        Assert.True(chat.IsComplete);
    }

    private static AgentChat Create3AgentChat()
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;

        return new(agent1, agent2, agent3);
    }

    private static Mock<LocalKernelAgent> CreateMockAgent()
    {
        Mock<LocalKernelAgent> agent = new(Kernel.CreateBuilder().Build(), "test");

        string id = Guid.NewGuid().ToString();
        ChatMessageContent[] messages = new[] { new ChatMessageContent(AuthorRole.Assistant, "test") };
        agent.SetupGet(a => a.Id).Returns(id);
        agent.Setup(a => a.InvokeAsync(It.IsAny<IEnumerable<ChatMessageContent>>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());

        return agent;
    }
}
