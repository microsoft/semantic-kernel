// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class HttpClientExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="threadId"></param>
    /// <param name="message"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadMessageModel?> CreateMessageAsync(
        this HttpClient httpClient,
        string threadId,
        ChatMessage message,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                role = message.Role,
                content = message.Content.ToString()
            };

        return
            httpClient.ExecutePostAsync<ThreadMessageModel>(
                GetMessagesUrl(threadId),
                payload,
                apiKey,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="threadId"></param>
    /// <param name="messageId"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadMessageModel?> GetMessageAsync(
        this HttpClient httpClient,
        string threadId,
        string messageId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<ThreadMessageModel>(
                GetMessagesUrl(threadId, messageId),
                apiKey,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="threadId"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<IList<ThreadMessageModel>?> GetMessagesAsync(
        this HttpClient httpClient,
        string threadId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<IList<ThreadMessageModel>>(
                GetMessagesUrl(threadId),
                apiKey,
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
