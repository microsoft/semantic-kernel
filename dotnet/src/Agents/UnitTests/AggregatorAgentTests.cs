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
        uberChat.Add(new ChatMessageContent(AuthorRole.User, "test uber"));

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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
>>>>>>> Stashed changes
<<<<<<< main
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
>>>>>>> ms/features/bugbash-prep
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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

<<<<<<< main
    private static MockAgent CreateMockAgent() => new() { Response = [new(AuthorRole.Assistant, "test")] };
=======
    private static Mock<ChatHistoryKernelAgent> CreateMockAgent()
    {
        Mock<ChatHistoryKernelAgent> agent = new();

        ChatMessageContent[] messages = [new ChatMessageContent(AuthorRole.Assistant, "test agent")];
        agent.Setup(a => a.InvokeAsync(It.IsAny<ChatHistory>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());
        agent.Setup(a => a.InvokeAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());

        return agent;
    }
>>>>>>> origin/PR
}
