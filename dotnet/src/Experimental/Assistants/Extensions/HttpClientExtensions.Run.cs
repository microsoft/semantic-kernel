// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using System.Threading;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class HttpClientExtensions
{
    public static Task<ThreadRunModel?> CreateRunAsync(
        this HttpClient httpClient,
        string threadId,
        string assistantId,
        string apiKey,
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
            httpClient.ExecutePostAsync<ThreadRunModel>(
                GetRunUrl(threadId),
                payload,
                apiKey,
                cancellationToken);
    }

    public static Task<ThreadRunModel?> GetRunAsync(
        this HttpClient httpClient,
        string threadId,
        string runId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<ThreadRunModel>(
                GetRunUrl(threadId, runId),
                apiKey,
                cancellationToken);
    }

    public static Task<IList<ThreadRunStepModel>?> GetRunStepsAsync(
        this HttpClient httpClient,
        string threadId,
        string runId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<IList<ThreadRunStepModel>>(
                GetRunStepsUrl(threadId, runId),
                apiKey,
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
