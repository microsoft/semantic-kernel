// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

/// <summary>
/// Supported OpenAI REST API actions for thread messages.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new message.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="message">The message</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message definition</returns>
    public static Task<ThreadMessageModel> CreateMessageAsync(
        this IOpenAIRestContext context,
        string threadId,
        ChatMessage message,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                role = message.Role,
                content = message.Content.ToString()
            };

        return
            context.ExecutePostAsync<ThreadMessageModel>(
                GetMessagesUrl(threadId),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an message by identifier.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messageId">The message identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message definition</returns>
    public static Task<ThreadMessageModel> GetMessageAsync(
        this IOpenAIRestContext context,
        string threadId,
        string messageId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadMessageModel>(
                GetMessagesUrl(threadId, messageId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve all thread messages.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A message list definition</returns>
    public static Task<ThreadRunStepListModel> GetMessagesAsync(
        this IOpenAIRestContext context,
        string threadId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadRunStepListModel>(
                GetMessagesUrl(threadId),
                cancellationToken);
    }

    private static string GetMessagesUrl(string threadId)
    {
        return $"{BaseThreadUrl}/{threadId}/messages";
    }

    private static string GetMessagesUrl(string threadId, string messageId)
    {
        return $"{BaseThreadUrl}/{threadId}/messages/{messageId}";
    }
}
