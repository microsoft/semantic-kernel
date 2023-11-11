// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using System.Net.Http;
using System.Threading.Tasks;
using System.Threading;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class HttpClientExtensions
{
    private const string BaseAssistantUrl = $"{BaseUrl}/assistants";

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="model"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<AssistantModel?> CreateAssistantAsync(
        this HttpClient httpClient,
        AssistantModel model,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecutePostAsync<AssistantModel>(
                BaseAssistantUrl,
                model,
                apiKey,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="assistantId"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<AssistantModel?> GetAssistantAsync(
        this HttpClient httpClient,
        string assistantId,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<AssistantModel>(
                GetAssistantUrl(assistantId),
                apiKey,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient"></param>
    /// <param name="apiKey"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<IList<AssistantModel>?> GetAssistantsAsync(
        this HttpClient httpClient,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return
            httpClient.ExecuteGetAsync<IList<AssistantModel>>(
                BaseAssistantUrl,
                apiKey,
                cancellationToken);
    }

    private static string GetAssistantUrl(string assistantId)
    {
        return $"{BaseAssistantUrl}/{assistantId}";
    }
}
