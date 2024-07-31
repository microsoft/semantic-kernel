// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistoryReducerExtensionsTests
{
    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)null);

        ChatHistory history = [];

        ChatHistory reducedHistory = await history.ReducedHistoryAsync(mockReducer.Object, default);

        Assert.StrictEqual(history, reducedHistory);

    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)[]);

        ChatHistory history = [];

        ChatHistory reducedHistory = await history.ReducedHistoryAsync(mockReducer.Object, default);

        Assert.NotStrictEqual(history, reducedHistory);

    }
}
