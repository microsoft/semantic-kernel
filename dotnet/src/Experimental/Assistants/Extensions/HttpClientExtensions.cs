// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class HttpClientExtensions
{
    public static async Task<TResult?> ExecuteGetAsync<TResult>(
        this HttpClient httpClient,
        string url,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreateGetRequest(url);

        request.Headers.Add("Authorization", $"Bearer {apiKey}");
        request.Headers.Add("OpenAI-Beta", "assistants=v1");

        using var response = await httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<TResult>(responseBody);
    }

    public static async Task<TResult?> ExecutePostAsync<TBody, TResult>(
        this HttpClient httpClient,
        string url,
        TBody payload,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreatePostRequest(url, payload);

        request.Headers.Add("Authorization", $"Bearer {apiKey}");
        request.Headers.Add("OpenAI-Beta", "assistants=v1");

        using var response = await httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<TResult>(responseBody);
    }
}
