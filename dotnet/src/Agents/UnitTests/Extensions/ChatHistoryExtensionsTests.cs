// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel;
using Xunit;
using System.Linq;
using System.Threading.Tasks;

namespace SemanticKernel.Agents.UnitTests.Extensions;

/// <summary>
/// Unit testing of <see cref="Microsoft.SemanticKernel.Agents.Extensions.ChatHistoryExtensions"/>.
/// </summary>
public class ChatHistoryExtensionsTests
{
    /// <summary>
    /// Verify ability to reverse history in-place.
    /// </summary>
    [Fact]
    public void VerifyChatHistoryOrdering()
    {
        ChatHistory history = [];
        history.AddUserMessage("Hi");
        history.AddAssistantMessage("Hi");

        VerifyRole(AuthorRole.User, history.First());
        VerifyRole(AuthorRole.Assistant, history.Last());

        VerifyRole(AuthorRole.User, history.ToDescending().Last());
        VerifyRole(AuthorRole.Assistant, history.ToDescending().First());
    }

    /// <summary>
    /// Verify ability to asynchronously reverse history in-place.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryOrderingAsync()
    {
        ChatHistory history = [];
        history.AddUserMessage("Hi");
        history.AddAssistantMessage("Hi");

        VerifyRole(AuthorRole.User, history.First());
        VerifyRole(AuthorRole.Assistant, history.Last());

        VerifyRole(AuthorRole.User, await history.ToDescendingAsync().LastOrDefaultAsync());
        VerifyRole(AuthorRole.Assistant, await history.ToDescendingAsync().FirstOrDefaultAsync());
    }

    private static void VerifyRole(AuthorRole expectedRole, ChatMessageContent? message)
    {
        Assert.Equal(expectedRole, message?.Role);
    }
}
