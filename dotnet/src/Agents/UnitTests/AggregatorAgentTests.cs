// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AggregatorAgent"/>.
/// </summary>
public class AggregatorAgentTests
{
    /// <summary>
    /// Verify usage of <see cref="AggregatorAgent"/> through various states.
    /// </summary>
    [Theory]
    [InlineData(AggregatorMode.Nested, 0)]
    [InlineData(AggregatorMode.Flat, 2)]
    public async Task VerifyAggregatorAgentUsageAsync(AggregatorMode mode, int modeOffset)
    {
        Agent agent1 = CreateMockAgent().Object;
        Agent agent2 = CreateMockAgent().Object;
        Agent agent3 = CreateMockAgent().Object;

        AgentGroupChat groupChat =
            new(agent1, agent2, agent3)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy =
                        {
                            MaximumIterations = 3
                        }
                    }
            };

        AggregatorAgent uberAgent = new(() => groupChat) { Mode = mode };
        AgentGroupChat uberChat = new();

        // Add message to outer chat (no agent has joined)
        uberChat.Add(new ChatMessageContent(AuthorRole.User, "test uber"));

        var messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Single(messages);

        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        Assert.Empty(messages); // Agent hasn't joined chat, no broadcast

        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Empty(messages); // Agent hasn't joined chat, no broadcast

        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));

        messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Single(messages);

        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        Assert.Empty(messages); // Agent still hasn't joined chat

        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Single(messages);

        // Invoke outer chat (outer chat captures final inner message)
        messages = await uberChat.InvokeAsync(uberAgent).ToArrayAsync();
        Assert.Equal(1 + modeOffset, messages.Length); // New messages generated from inner chat

        messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(2 + modeOffset, messages.Length); // Total messages on uber chat

        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(5, messages.Length); // Total messages on inner chat once synchronized

        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        Assert.Equal(5, messages.Length); // Total messages on inner chat once synchronized (agent equivalent)
    }

    private static Mock<ChatHistoryKernelAgent> CreateMockAgent()
    {
        Mock<ChatHistoryKernelAgent> agent = new();

        ChatMessageContent[] messages = [new ChatMessageContent(AuthorRole.Assistant, "test agent")];
        agent.Setup(a => a.InvokeAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), It.IsAny<ILogger>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());

        return agent;
    }
}
