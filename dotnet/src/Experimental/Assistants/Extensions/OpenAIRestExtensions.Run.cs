// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="instructions">Optional instruction override</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> CreateRunAsync(
        this IOpenAIRestContext context,
        string threadId,
        string assistantId,
        string? instructions,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                assistant_id = assistantId,
                instructions,
                //tools = tools // TODO: @chris FUNCTIONS
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
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
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
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">A run identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A set of run steps</returns>
    public static Task<ThreadRunStepListModel> GetRunStepsAsync(
        this IOpenAIRestContext context,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<ThreadRunStepListModel>(
                GetRunStepsUrl(threadId, runId),
                cancellationToken);
    }

    /// <summary>
    /// Add a function result for a run.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">A thread identifier</param>
    /// <param name="runId">The run identifier</param>
    /// <param name="callId">The tool-call identifier</param>
    /// <param name="result">The function/tool result.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A run definition</returns>
    public static Task<ThreadRunModel> AddToolOutputAsync(
        this IOpenAIRestContext context,
        string threadId,
        string runId,
        string callId, // $$$ ARRAY
        object result, // $$$ ARRAY
        CancellationToken cancellationToken = default)
    {
        var payload =
           new
           {
               tool_outputs =
                   new[]
                   {
                        new
                        {
                            tool_call_id = callId,
                            output = result
                        }
                   }
           };

        return
            context.ExecutePostAsync<ThreadRunModel>(
                GetRunToolOutput(threadId, runId),
                payload,
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

    private static string GetRunToolOutput(string threadId, string runId)
    {
        return $"{BaseThreadUrl}/{threadId}/runs/{runId}/submit_tool_outputs";
    }
}
