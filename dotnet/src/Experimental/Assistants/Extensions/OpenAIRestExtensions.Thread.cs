// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

/// <summary>
/// Supported OpenAI REST API actions for threads.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    private const string BaseThreadUrl = $"{BaseUrl}/threads";

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A thread definition</returns>
    public static Task<ThreadModel> CreateThreadModelAsync(
        this IOpenAIRestContext context,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecutePostAsync<ThreadModel>(
                BaseThreadUrl,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an thread by identifier.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A thread definition</returns>
    public static Task<ThreadModel> GetThreadModelAsync(
        this IOpenAIRestContext context,
        string threadId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadModel>(
                GetThreadUrl(threadId),
                cancellationToken);
    }

    private static string GetThreadUrl(string threadId)
    {
        return $"{BaseThreadUrl}/{threadId}";
    }
}
