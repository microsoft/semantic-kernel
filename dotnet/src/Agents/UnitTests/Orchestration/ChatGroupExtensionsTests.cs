// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

public class ChatGroupExtensionsTests
{
    [Fact]
    public void FormatNames_WithMultipleAgents_ReturnsCommaSeparatedList()
    {
        // Arrange
        ChatGroup group = new()
        {
            { "agent1", ("Agent One", "First agent description") },
            { "agent2", ("Agent Two", "Second agent description") },
            { "agent3", ("Agent Three", "Third agent description") }
        };

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal("Agent One,Agent Two,Agent Three", result);
    }

    [Fact]
    public void FormatNames_WithSingleAgent_ReturnsSingleName()
    {
        // Arrange
        ChatGroup group = new()
        {
            { "agent1", ("Agent One", "First agent description") }
        };

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal("Agent One", result);
    }

    [Fact]
    public void FormatNames_WithEmptyGroup_ReturnsEmptyString()
    {
        // Arrange
        ChatGroup group = [];

        // Act
        string result = group.FormatNames();

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void FormatList_WithMultipleAgents_ReturnsMarkdownList()
    {
        // Arrange
        ChatGroup group = new()
        {
            { "agent1", ("Agent One", "First agent description") },
            { "agent2", ("Agent Two", "Second agent description") },
            { "agent3", ("Agent Three", "Third agent description") }
        };

        // Act
        string result = group.FormatList();

        // Assert
        const string Expected =
            """
            - Agent One: First agent description
            - Agent Two: Second agent description
            - Agent Three: Third agent description
            """;
        Assert.Equal(Expected, result);
    }

    [Fact]
    public void FormatList_WithEmptyGroup_ReturnsEmptyString()
    {
        // Arrange
        ChatGroup group = [];

        // Act & Assert
        Assert.Equal(string.Empty, group.FormatNames());
        Assert.Equal(string.Empty, group.FormatList());
    }
}
