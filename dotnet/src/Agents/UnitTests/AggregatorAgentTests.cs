<<<<<<< main
// Copyright (c) Microsoft. All rights reserved.
=======
﻿// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
>>>>>>> upstream/main
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
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
        Agent agent1 = CreateMockAgent("First");
        Agent agent2 = CreateMockAgent("Second");
        Agent agent3 = CreateMockAgent("Third");

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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
>>>>>>> Stashed changes
=======
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        // Add message to inner chat (not visible to parent)
        groupChat.Add(new ChatMessageContent(AuthorRole.User, "test inner"));
=======
>>>>>>> ms/features/bugbash-prep
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
=======
    /// <summary>
    /// Ensure multiple <see cref="AggregatorAgent"/> instances do not share a channel.
    /// </summary>
    [Fact]
    public async Task VerifyMultipleAggregatorAgentAsync()
    {
        const string UserInput = "User Input";

        // Arrange
        Agent agent1Exec = CreateMockAgent("agent1 exec");
        Agent agent1Review = CreateMockAgent("agent1 [OK]");
        Agent agent2Exec = CreateMockAgent("agent2 exec");
        Agent agent2Review = CreateMockAgent("agent2 [OK]");

        AgentGroupChat agent1Chat =
            new(agent1Exec, agent1Review)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy = new ApprovalTerminationStrategy()
                        {
                            Agents = [agent1Review],
                            MaximumIterations = 3,
                            AutomaticReset = true,
                        }
                    }
            };
        AgentGroupChat agent2Chat =
            new(agent2Exec, agent2Review)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy = new ApprovalTerminationStrategy()
                        {
                            Agents = [agent2Review],
                            MaximumIterations = 4,
                            AutomaticReset = false,
                        }
                    }
            };

        AggregatorAgent agent1 = new(() => agent1Chat) { Mode = AggregatorMode.Flat, Name = "agent1" };
        AggregatorAgent agent2 = new(() => agent2Chat) { Mode = AggregatorMode.Flat, Name = "agent2" };
        AgentGroupChat userChat = new(agent1, agent2)
        {
            ExecutionSettings =
                new()
                {
                    TerminationStrategy = new AgentTerminationStrategy(agent2)
                    {
                        MaximumIterations = 8,
                        AutomaticReset = true
                    }
                }
        };

        userChat.AddChatMessage(new ChatMessageContent(AuthorRole.User, UserInput));

        // Act
        ChatMessageContent[] messages = await userChat.InvokeAsync().ToArrayAsync();

        // Assert
        Assert.Equal(4, messages.Length);
        Assert.Equal(agent1Exec.Name, messages[0].AuthorName);
        Assert.Equal(agent1Review.Name, messages[1].AuthorName);
        Assert.Equal(agent2Exec.Name, messages[2].AuthorName);
        Assert.Equal(agent2Review.Name, messages[3].AuthorName);
    }

    private static MockAgent CreateMockAgent(string agentName) => new() { Name = agentName, Response = [new(AuthorRole.Assistant, $"{agentName} -> test") { AuthorName = agentName }] };

    private sealed class ApprovalTerminationStrategy : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(history[history.Count - 1].Content?.Contains("[OK]", StringComparison.OrdinalIgnoreCase) ?? false);
    }

    private sealed class AgentTerminationStrategy(Agent lastAgent) : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(agent == lastAgent);
        }
    }
>>>>>>> upstream/main
}
