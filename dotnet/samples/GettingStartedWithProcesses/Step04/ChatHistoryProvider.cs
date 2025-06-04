// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step04;

/// <summary>
/// Provider based access to the chat history.
/// </summary>
/// <remarks>
/// While the in-memory implementation is trivial, this abstraction demonstrates how one might
/// allow for the ability to access chat history from a remote store for a distributed service.
/// <code>
/// class CosmosDbChatHistoryProvider(CosmosClient client, string sessionId) : IChatHistoryProvider { }
/// </code>
/// </remarks>
internal interface IChatHistoryProvider
{
    /// <summary>
    /// Provides access to the chat history.
    /// </summary>
    Task<ChatHistory> GetHistoryAsync();

    /// <summary>
    /// Commits any updates to the chat history.
    /// </summary>
    Task CommitAsync();
}

/// <summary>
/// In memory based specialization of <see cref="IChatHistoryProvider"/>.
/// </summary>
internal sealed class ChatHistoryProvider(ChatHistory history) : IChatHistoryProvider
{
    /// <inheritdoc/>
    public Task<ChatHistory> GetHistoryAsync() => Task.FromResult(history);

    /// <inheritdoc/>
    public Task CommitAsync()
    {
        return Task.CompletedTask;
    }
}
