// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Supported OpenAI REST API actions for threads.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A thread definition</returns>
    public static Task<ThreadModel> CreateThreadModelAsync(
        this OpenAIRestContext context,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecutePostAsync<ThreadModel>(
                context.GetThreadsUrl(),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an thread by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A thread definition</returns>
    public static Task<ThreadModel> GetThreadModelAsync(
        this OpenAIRestContext context,
        string threadId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadModel>(
                context.GetThreadUrl(threadId),
                cancellationToken);
    }

    /// <summary>
    /// Delete an existing thread.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="id">Identifier of thread to delete</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static Task DeleteThreadModelAsync(
        this OpenAIRestContext context,
        string id,
        CancellationToken cancellationToken = default)
    {
        return context.ExecuteDeleteAsync(context.GetThreadUrl(id), cancellationToken);
    }

    internal static string GetThreadsUrl(this OpenAIRestContext context) => $"{context.Endpoint}/threads";

    internal static string GetThreadUrl(this OpenAIRestContext context, string threadId) => $"{context.Endpoint}/threads/{threadId}";
}
