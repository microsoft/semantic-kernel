// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class HttpClientExtensions
{
    private const string BaseThreadUrl = $"{BaseUrl}/threads";

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadModel?> CreateThreadAsync(
        this HttpClient httpClient,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecutePostAsync<ThreadModel>(
                BaseThreadUrl,
                apiKey,
                cancellationToken);
    }

    public static Task<ThreadModel?> GetThreadAsync(
        this HttpClient httpClient,
        string threadId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<ThreadModel>(
                GetThreadUrl(threadId),
                apiKey,
                cancellationToken);
    }

    private static string GetThreadUrl(string threadId)
    {
        return $"{BaseThreadUrl}/{threadId}";
    }
}
