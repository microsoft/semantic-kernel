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

        (bool isReduced, ChatHistory reducedHistory) = await history.ReduceHistoryAsync(mockReducer.Object, default);

        Assert.False(isReduced);
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

        (bool isReduced, ChatHistory reducedHistory) = await history.ReduceHistoryAsync(mockReducer.Object, default);

        Assert.True(isReduced);
        Assert.NotStrictEqual(history, reducedHistory);
    }
}
