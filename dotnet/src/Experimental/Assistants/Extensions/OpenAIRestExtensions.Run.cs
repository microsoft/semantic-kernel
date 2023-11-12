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
    /// <param name="assistantId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
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
                //instructions = kernel.Instructions, $$$
                //tools = tools
            };

        return
            context.ExecutePostAsync<ThreadRunModel>(
                GetRunUrl(threadId),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="runId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
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
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="runId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
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
