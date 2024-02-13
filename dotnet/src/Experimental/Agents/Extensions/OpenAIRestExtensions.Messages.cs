// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Supported OpenAI REST API actions for thread messages.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new message.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="content">The message text</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message definition</returns>
    public static Task<ThreadMessageModel> CreateUserTextMessageAsync(
        this OpenAIRestContext context,
        string threadId,
        string content,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                role = AuthorRole.User.Label,
                content,
            };

        return
            context.ExecutePostAsync<ThreadMessageModel>(
                context.GetMessagesUrl(threadId),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an message by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messageId">The message identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message definition</returns>
    public static Task<ThreadMessageModel> GetMessageAsync(
        this OpenAIRestContext context,
        string threadId,
        string messageId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadMessageModel>(
                context.GetMessagesUrl(threadId, messageId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve all thread messages.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message list definition</returns>
    public static Task<ThreadMessageListModel> GetMessagesAsync(
        this OpenAIRestContext context,
        string threadId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadMessageListModel>(
                context.GetMessagesUrl(threadId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve all thread messages.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messageIds">The set of message identifiers to retrieve</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message list definition</returns>
    public static async Task<IEnumerable<ThreadMessageModel>> GetMessagesAsync(
        this OpenAIRestContext context,
        string threadId,
        IEnumerable<string> messageIds,
        CancellationToken cancellationToken = default)
    {
        var tasks =
            messageIds.Select(
                id =>
                    context.ExecuteGetAsync<ThreadMessageModel>(
                        context.GetMessagesUrl(threadId, id),
                        cancellationToken)).ToArray();

        await Task.WhenAll(tasks).ConfigureAwait(false);

        return tasks.Select(t => t.Result).ToArray();
    }

    internal static string GetMessagesUrl(this OpenAIRestContext context, string threadId)
    {
        return $"{context.GetThreadUrl(threadId)}/messages";
    }

    internal static string GetMessagesUrl(this OpenAIRestContext context, string threadId, string messageId)
    {
        return $"{context.GetThreadUrl(threadId)}/messages/{messageId}";
    }
}
