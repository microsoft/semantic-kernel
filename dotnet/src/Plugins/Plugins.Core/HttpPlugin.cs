﻿// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// A plugin that provides HTTP functionality.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings",
    Justification = "Semantic Kernel operates on strings")]
public sealed class HttpPlugin
{
    private readonly HttpClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpPlugin"/> class.
    /// </summary>
    public HttpPlugin() : this(null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpPlugin"/> class.
    /// </summary>
    /// <param name="client">The HTTP client to use.</param>
    /// <remarks>
    /// <see cref="HttpPlugin"/> assumes ownership of the <see cref="HttpClient"/> instance and will dispose it when the plugin is disposed.
    /// </remarks>
    [ActivatorUtilitiesConstructor]
    public HttpPlugin(HttpClient? client = null) =>
        this._client = client ?? HttpClientProvider.GetHttpClient();

    /// <summary>
    /// Sends an HTTP GET request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [KernelFunction, Description("Makes a GET request to a uri")]
    public Task<string> GetAsync(
        [Description("The URI of the request")] string uri,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Get, requestContent: null, cancellationToken);

    /// <summary>
    /// Sends an HTTP POST request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="body">The body of the request</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [KernelFunction, Description("Makes a POST request to a uri")]
    public Task<string> PostAsync(
        [Description("The URI of the request")] string uri,
        [Description("The body of the request")] string body,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Post, new StringContent(body), cancellationToken);

    /// <summary>
    /// Sends an HTTP PUT request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="body">The body of the request</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [KernelFunction, Description("Makes a PUT request to a uri")]
    public Task<string> PutAsync(
        [Description("The URI of the request")] string uri,
        [Description("The body of the request")] string body,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Put, new StringContent(body), cancellationToken);

    /// <summary>
    /// Sends an HTTP DELETE request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>The response body as a string.</returns>
    [KernelFunction, Description("Makes a DELETE request to a uri")]
    public Task<string> DeleteAsync(
        [Description("The URI of the request")] string uri,
        CancellationToken cancellationToken = default) =>
        this.SendRequestAsync(uri, HttpMethod.Delete, requestContent: null, cancellationToken);

    /// <summary>Sends an HTTP request and returns the response content as a string.</summary>
    /// <param name="uri">The URI of the request.</param>
    /// <param name="method">The HTTP method for the request.</param>
    /// <param name="requestContent">Optional request content.</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    private async Task<string> SendRequestAsync(string uri, HttpMethod method, HttpContent? requestContent, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(method, uri) { Content = requestContent };
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(HttpPlugin)));
        using var response = await this._client.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);
    }
}
