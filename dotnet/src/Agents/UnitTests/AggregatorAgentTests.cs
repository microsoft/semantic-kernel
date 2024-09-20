// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
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
        // Arrange
        Agent agent1 = CreateMockAgent();
        Agent agent2 = CreateMockAgent();
        Agent agent3 = CreateMockAgent();

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
        uberChat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test uber"));

        // Act
        var messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Act
        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        // Assert
        Assert.Empty(messages); // Agent hasn't joined chat, no broadcast

        // Act
        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Empty(messages); // Agent hasn't joined chat, no broadcast

        // Arrange: Add message to inner chat (not visible to parent)
        groupChat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test inner"));

        // Act
        messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Act
        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        // Assert
        Assert.Empty(messages); // Agent still hasn't joined chat

        // Act
        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Act: Invoke outer chat (outer chat captures final inner message)
        messages = await uberChat.InvokeAsync(uberAgent).ToArrayAsync();
        // Assert
        Assert.Equal(1 + modeOffset, messages.Length); // New messages generated from inner chat

        // Act
        messages = await uberChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Equal(2 + modeOffset, messages.Length); // Total messages on uber chat

        // Act
        messages = await groupChat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Equal(5, messages.Length); // Total messages on inner chat once synchronized

        // Act
        messages = await uberChat.GetChatMessagesAsync(uberAgent).ToArrayAsync();
        // Assert
        Assert.Equal(5, messages.Length); // Total messages on inner chat once synchronized (agent equivalent)
    }

    private static MockAgent CreateMockAgent() => new() { Response = [new(AuthorRole.Assistant, "test")] };
}
