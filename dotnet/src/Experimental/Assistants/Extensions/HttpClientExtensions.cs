// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class HttpClientExtensions
{
    private const string BaseUrl = "https://api.openai.com/v1/";
    private const string HeaderNameOpenAIAssistant = "OpenAI-Beta";
    private const string HeaderNameAuthorization = "Authorization";
    private const string HeaderOpenAIValueAssistant = "assistants=v1";

    public static async Task<TResult?> ExecuteGetAsync<TResult>(
        this HttpClient httpClient,
        string url,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreateGetRequest(url);

        request.Headers.Add(HeaderNameAuthorization, $"Bearer {apiKey}");
        request.Headers.Add(HeaderNameOpenAIAssistant, HeaderOpenAIValueAssistant);

        using var response = await httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<TResult>(responseBody);
    }

    public static Task<TResult?> ExecutePostAsync<TResult>(
        this HttpClient httpClient,
        string url,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        return httpClient.ExecutePostAsync<TResult>(url, payload: null, apiKey, cancellationToken);
    }

    public static async Task<TResult?> ExecutePostAsync<TResult>(
        this HttpClient httpClient,
        string url,
        object? payload,
        string apiKey,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreatePostRequest(url, payload);

        request.Headers.Add(HeaderNameAuthorization, $"Bearer {apiKey}");
        request.Headers.Add(HeaderNameOpenAIAssistant, HeaderOpenAIValueAssistant);

        using var response = await httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<TResult>(responseBody);
    }
}
