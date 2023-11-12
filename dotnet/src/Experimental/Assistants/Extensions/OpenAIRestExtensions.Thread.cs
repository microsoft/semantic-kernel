// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class OpenAIRestExtensions
{
    private const string BaseThreadUrl = $"{BaseUrl}/threads";

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadModel> CreateThreadAsync(
        this IOpenAIRestContext context,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecutePostAsync<ThreadModel>(
                BaseThreadUrl,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="threadId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<ThreadModel> GetThreadAsync(
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
