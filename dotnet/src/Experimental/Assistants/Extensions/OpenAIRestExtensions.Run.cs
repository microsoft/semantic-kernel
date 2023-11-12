// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

/// <summary>
/// Supported OpenAI REST API actions for thread runs.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new run.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> CreateRunAsync(
        this IOpenAIRestContext context,
        string threadId,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                assistant_id = assistantId,
                //instructions = kernel.Instructions, // $$$ TBD
                //tools = tools // $$$ TBD
            };

        return
            context.ExecutePostAsync<ThreadRunModel>(
                GetRunUrl(threadId),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an run by identifier.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">A run identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> GetRunAsync(
        this IOpenAIRestContext context,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadRunModel>(
                GetRunUrl(threadId, runId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve run steps by identifier.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">A run identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A set of run steps</returns>
    public static Task<IList<ThreadRunStepModel>> GetRunStepsAsync(
        this IOpenAIRestContext context,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<IList<ThreadRunStepModel>>(
                GetRunStepsUrl(threadId, runId),
                cancellationToken);
    }

    private static string GetRunUrl(string threadId)
    {
        return $"{BaseThreadUrl}/{threadId}/runs";
    }

    private static string GetRunUrl(string threadId, string runId)
    {
        return $"{BaseThreadUrl}/{threadId}/runs/{runId}";
    }

    private static string GetRunStepsUrl(string threadId, string runId)
    {
        return $"{BaseThreadUrl}/{threadId}/runs/{runId}/steps";
    }
}
