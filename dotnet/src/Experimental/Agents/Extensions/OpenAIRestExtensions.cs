// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Experimental.Agents;

internal static partial class OpenAIRestExtensions
{
    private const string HeaderNameOpenAIAssistant = "OpenAI-Beta";
    private const string HeaderNameAuthorization = "Authorization";
    private const string HeaderOpenAIValueAssistant = "assistants=v1";

    private static Task<TResult> ExecuteGetAsync<TResult>(
        this OpenAIRestContext context,
        string url,
        CancellationToken cancellationToken = default)
    {
        return context.ExecuteGetAsync<TResult>(url, query: null, cancellationToken);
    }

    private static async Task<TResult> ExecuteGetAsync<TResult>(
        this OpenAIRestContext context,
        string url,
        string? query = null,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreateGetRequest(context.FormatUrl(url, query));

        request.AddHeaders(context);

        using var response = await context.GetHttpClient().SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var responseBody = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        // Common case is for failure exception to be raised by REST invocation.
        // Null result is a logical possibility, but unlikely edge case.
        // Might occur due to model alignment issues over time.
        return
            JsonSerializer.Deserialize<TResult>(responseBody) ??
            throw new AgentException($"Null result processing: {typeof(TResult).Name}");
    }

    private static Task<TResult> ExecutePostAsync<TResult>(
        this OpenAIRestContext context,
        string url,
        CancellationToken cancellationToken = default)
    {
        return context.ExecutePostAsync<TResult>(url, payload: null, cancellationToken);
    }

    private static async Task<TResult> ExecutePostAsync<TResult>(
        this OpenAIRestContext context,
        string url,
        object? payload,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreatePostRequest(context.FormatUrl(url), payload);

        request.AddHeaders(context);

        using var response = await context.GetHttpClient().SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var responseBody = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return
            JsonSerializer.Deserialize<TResult>(responseBody) ??
            throw new AgentException($"Null result processing: {typeof(TResult).Name}");
    }

    private static async Task ExecuteDeleteAsync(
        this OpenAIRestContext context,
        string url,
        CancellationToken cancellationToken = default)
    {
        using var request = HttpRequest.CreateDeleteRequest(context.FormatUrl(url));

        request.AddHeaders(context);

        using var response = await context.GetHttpClient().SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private static void AddHeaders(this HttpRequestMessage request, OpenAIRestContext context)
    {
        if (context.HasVersion)
        {
            // OpenAI
            request.Headers.Add("api-key", context.ApiKey);
        }

        // Azure OpenAI
        request.Headers.Add(HeaderNameAuthorization, $"Bearer {context.ApiKey}");
        request.Headers.Add(HeaderNameOpenAIAssistant, HeaderOpenAIValueAssistant);
    }

    private static string FormatUrl(
        this OpenAIRestContext context,
        string url,
        string? query = null)
    {
        var hasQuery = !string.IsNullOrWhiteSpace(query);
        var delimiter = hasQuery ? "?" : string.Empty;

        if (!context.HasVersion)
        {
            // OpenAI
            return $"{url}{delimiter}{query}";
        }

        // Azure OpenAI
        var delimiterB = hasQuery ? "&" : "?";

        return $"{url}{delimiter}{query}{delimiterB}api-version={context.Version}";
    }
}
