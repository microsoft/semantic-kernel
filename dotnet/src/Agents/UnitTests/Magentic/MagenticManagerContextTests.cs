// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Magentic;

public class MagenticManagerContextTests
{
    [Fact]
    public void Constructor_ShouldInitializeAllProperties()
    {
        // Arrange
        MagenticTeam mockTeam = [];
        List<ChatMessageContent> task = [new ChatMessageContent(AuthorRole.User, "Test task")];
        List<ChatMessageContent> history =
        [
            new ChatMessageContent(AuthorRole.User, "Test message 1"),
            new ChatMessageContent(AuthorRole.Assistant, "Test response 1")
        ];

        const int ResponseCount = 5;
        const int StallCount = 2;
        const int ResetCount = 1;

        // Act
        MagenticManagerContext context = new(mockTeam, task, history, ResponseCount, StallCount, ResetCount);

        // Assert
        Assert.Equal(mockTeam, context.Team);
        Assert.Equal(task, context.Task);
        Assert.Equal(history, context.History);
        Assert.Equal(ResponseCount, context.ResponseCount);
        Assert.Equal(StallCount, context.StallCount);
        Assert.Equal(ResetCount, context.ResetCount);
    }

    [Fact]
    public void ReadOnlyCollections_ShouldNotAllowModification()
    {
        // Arrange
        MagenticTeam mockTeam = [];
        List<ChatMessageContent> task = [new ChatMessageContent(AuthorRole.User, "Test task")];
        List<ChatMessageContent> history = [new ChatMessageContent(AuthorRole.User, "Test message")];

        // Act
        MagenticManagerContext context = new(mockTeam, task, history, 0, 0, 0);

        // Assert
        // Verify that the collections exposed as IReadOnlyList don't allow modifications
        Assert.Throws<NotSupportedException>(() => ((IList<ChatMessageContent>)context.History).Add(new ChatMessageContent(AuthorRole.User, "New history")));
        Assert.Throws<NotSupportedException>(() => ((IList<ChatMessageContent>)context.Task).Add(new ChatMessageContent(AuthorRole.User, "New task")));
    }
}
