// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Core;

/// <summary>
/// A skill that provides HTTP functionality.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("http", new HttpSkill());
/// Examples:
/// SKContext["url"] = "https://www.bing.com"
/// {{http.getAsync $url}}
/// {{http.postAsync $url}}
/// {{http.putAsync $url}}
/// {{http.deleteAsync $url}}
/// </example>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings",
    Justification = "Semantic Kernel operates on strings")]
public sealed class HttpSkill : IDisposable
{
    private readonly HttpClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    public HttpSkill() : this(new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false))
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    /// <param name="client">The HTTP client to use.</param>
    /// <remarks>
    /// <see cref="HttpSkill"/> assumes ownership of the <see cref="HttpClient"/> instance and will dispose it when the skill is disposed.
    /// </remarks>
    public HttpSkill(HttpClient client) =>
        this._client = client;

    /// <summary>
    /// Sends an HTTP GET request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request.</param>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction, Description("Makes a GET request to a uri")]
    public Task<string> GetAsync(
        [Description("The URI of the request")] string uri,
        [Description("Optional headers for the request of keyVaulePair List type in serialized form")] string? serializedHeaders = null,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Get, null, serializedHeaders, cancellationToken);

    /// <summary>
    /// Sends an HTTP POST request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request.</param>
    /// <param name="body">The body of the request.</param>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction, Description("Makes a POST request to a uri")]
    public Task<string> PostAsync(
        [Description("The URI of the request")] string uri,
        [Description("The body of the request")] string body,
        [Description("Optional headers for the request of keyVaulePair List type in serialized form")] string? serializedHeaders = null,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Post, new StringContent(body), serializedHeaders, cancellationToken);

    /// <summary>
    /// Sends an HTTP PUT request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request.</param>
    /// <param name="body">The body of the request.</param>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction, Description("Makes a PUT request to a uri")]
    public Task<string> PutAsync(
        [Description("The URI of the request")] string uri,
        [Description("The body of the request")] string body,
        [Description("Optional headers for the request of keyVaulePair List type in serialized form")] string? serializedHeaders = null,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Put, new StringContent(body), serializedHeaders, cancellationToken);

    /// <summary>
    /// Sends an HTTP DELETE request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction, Description("Makes a DELETE request to a uri")]
    public Task<string> DeleteAsync(
        [Description("The URI of the request")] string uri,
        [Description("Optional headers for the request of keyVaulePair List type in serialized form")] string? serializedHeaders = null,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Delete, null, serializedHeaders, cancellationToken);

    /// <summary>Sends an HTTP request and returns the response content as a string.</summary>
    /// <param name="uri">The URI of the request.</param>
    /// <param name="method">The HTTP method for the request.</param>
    /// <param name="requestContent">Optional request content.</param>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    private async Task<string> SendRequestAsync(string uri, HttpMethod method, HttpContent? requestContent, string? serializedHeaders, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(method, uri) { Content = requestContent };
        foreach (KeyValuePair<string, string> header in this.GetHeadersList(serializedHeaders))
        {
            request.Headers.Add(header.Key, header.Value);
        }
        using var response = await this._client.SendAsync(request, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
    }

    /// <summary>Deserializes the Http headers string and returns the header list.</summary>
    /// <param name="serializedHeaders">Optional headers for the request of keyVaulePair List type in in serialized form using System.Text.Json</param>
    private List<KeyValuePair<string, string>> GetHeadersList(string? serializedHeaders)
    {
        List<KeyValuePair<string, string>> headers = new();
        if (string.IsNullOrEmpty(serializedHeaders))
        {
            return headers;
        }
        List<KeyValuePair<string, string>>? deserializedHeaders = JsonSerializer.Deserialize<List<KeyValuePair<string, string>>>(serializedHeaders);
        if (deserializedHeaders == null)
        {
            return headers;
        }
        return deserializedHeaders;
    }

    /// <summary>
    /// Disposes resources
    /// </summary>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. There is no longer a need to invoke this method, and its call can be safely omitted.")]
    public void Dispose()
    {
    }
}
