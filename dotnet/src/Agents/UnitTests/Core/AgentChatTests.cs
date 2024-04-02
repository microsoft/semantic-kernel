// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
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
    /// $$$
    /// </summary>
    [Fact]
    public void VerifyAgentChatDefaultStateAsync()
    {
        AgentChat chat = new();
        Assert.Empty(chat.Agents);
        Assert.Null(chat.ExecutionSettings);
        Assert.False(chat.IsComplete);
    }

    /// <summary>
    /// $$$
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

        var messages = await chat.InvokeAsync(agent4, "test").ToArrayAsync();
        Assert.Equal(3, chat.Agents.Count);

        messages = await chat.InvokeAsync(agent4, isJoining: true).ToArrayAsync();
        Assert.Equal(4, chat.Agents.Count);
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
