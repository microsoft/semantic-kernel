// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="message"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadMessageModel?> CreateMessageAsync(
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
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="messageId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadMessageModel?> GetMessageAsync(
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
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<IList<ThreadMessageModel>?> GetMessagesAsync(
        this IOpenAIRestContext context,
        string threadId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<IList<ThreadMessageModel>>(
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
