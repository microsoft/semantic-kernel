// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Supported OpenAI REST API actions for thread runs.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new run.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="instructions">Optional instruction override</param>
    /// <param name="tools">The assistant tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> CreateRunAsync(
        this OpenAIRestContext context,
        string threadId,
        string assistantId,
        string? instructions = null,
        IEnumerable<ToolModel>? tools = null,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                assistant_id = assistantId,
                instructions,
                tools,
            };

        return
            context.ExecutePostAsync<ThreadRunModel>(
                context.GetRunsUrl(threadId),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an run by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">A run identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> GetRunAsync(
        this OpenAIRestContext context,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadRunModel>(
                context.GetRunUrl(threadId, runId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve run steps by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">A run identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A set of run steps</returns>
    public static Task<ThreadRunStepListModel> GetRunStepsAsync(
        this OpenAIRestContext context,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadRunStepListModel>(
                context.GetRunStepsUrl(threadId, runId),
                cancellationToken);
    }

    /// <summary>
    /// Add a function result for a run.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">The run identifier</param>
    /// <param name="results">The function/tool results.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> AddToolOutputsAsync(
        this OpenAIRestContext context,
        string threadId,
        string runId,
        IEnumerable<ToolResultModel> results,
        CancellationToken cancellationToken = default)
    {
        var payload =
           new
           {
               tool_outputs = results
           };

        return
            context.ExecutePostAsync<ThreadRunModel>(
                context.GetRunToolOutputUrl(threadId, runId),
                payload,
                cancellationToken);
    }

    internal static string GetRunsUrl(this OpenAIRestContext context, string threadId)
    {
        return $"{context.GetThreadUrl(threadId)}/runs";
    }

    internal static string GetRunUrl(this OpenAIRestContext context, string threadId, string runId)
    {
        return $"{context.GetThreadUrl(threadId)}/runs/{runId}";
    }

    internal static string GetRunStepsUrl(this OpenAIRestContext context, string threadId, string runId)
    {
        return $"{context.GetThreadUrl(threadId)}/runs/{runId}/steps";
    }

    internal static string GetRunToolOutputUrl(this OpenAIRestContext context, string threadId, string runId)
    {
        return $"{context.GetThreadUrl(threadId)}/runs/{runId}/submit_tool_outputs";
    }
}
