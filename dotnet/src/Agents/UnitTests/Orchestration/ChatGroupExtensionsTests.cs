// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

public class ChatGroupExtensionsTests
{
    [Fact]
    public void FormatNames_WithMultipleAgents_ReturnsCommaSeparatedList()
    {
        // Arrange
        GroupChatTeam group = new()
        {
            { "AgentOne", ("agent1", "First agent description") },
            { "AgentTwo", ("agent2", "Second agent description") },
            { "AgentThree", ("agent3", "Third agent description") }
        };

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal("AgentOne,AgentTwo,AgentThree", result);
    }

    [Fact]
    public void FormatNames_WithSingleAgent_ReturnsSingleName()
    {
        // Arrange
        GroupChatTeam group = new()
        {
            { "AgentOne", ("agent1", "First agent description") },
        };

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal("AgentOne", result);
    }

    [Fact]
    public void FormatNames_WithEmptyGroup_ReturnsEmptyString()
    {
        // Arrange
        GroupChatTeam group = [];

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void FormatList_WithMultipleAgents_ReturnsMarkdownList()
    {
        // Arrange
        GroupChatTeam group = new()
        {
            { "AgentOne", ("agent1", "First agent description") },
            { "AgentTwo", ("agent2", "Second agent description") },
            { "AgentThree", ("agent3", "Third agent description") }
        };

        // Act
        string result = group.FormatList();

        // Assert
        const string Expected =
            """
            - AgentOne: First agent description
            - AgentTwo: Second agent description
            - AgentThree: Third agent description
            """;
        Assert.Equal(Expected, result);
    }

    [Fact]
    public void FormatList_WithEmptyGroup_ReturnsEmptyString()
    {
        // Arrange
        GroupChatTeam group = [];

        // Act & Assert
        Assert.Equal(string.Empty, group.FormatNames());
        Assert.Equal(string.Empty, group.FormatList());
    }
}
