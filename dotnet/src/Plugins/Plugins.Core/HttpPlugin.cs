// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
/// <remarks>
/// <para>
/// This plugin is secure by default. <see cref="AllowedDomains"/> must be explicitly configured
/// before any HTTP requests are permitted. By default, all domains are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedDomains"/> is restricted to trusted values only.
/// </para>
/// </remarks>
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
    /// List of allowed domains to send requests to.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no domains allowed). Must be explicitly populated
    /// with trusted domains before any requests will succeed.
    /// </remarks>
    public IEnumerable<string>? AllowedDomains
    {
        get => this._allowedDomains;
        set => this._allowedDomains = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

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

    #region private
    private HashSet<string>? _allowedDomains = [];

    /// <summary>
    /// If a list of allowed domains has been provided, the host of the provided uri is checked
    /// to verify it is in the allowed domain list.
    /// </summary>
    private bool IsUriAllowed(Uri uri)
    {
        Verify.NotNull(uri);

        return this._allowedDomains is not null
            && this._allowedDomains.Count > 0
            && this._allowedDomains.Contains(uri.Host);
    }

    /// <summary>Sends an HTTP request and returns the response content as a string.</summary>
    /// <param name="uriStr">The URI of the request.</param>
    /// <param name="method">The HTTP method for the request.</param>
    /// <param name="requestContent">Optional request content.</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    private async Task<string> SendRequestAsync(string uriStr, HttpMethod method, HttpContent? requestContent, CancellationToken cancellationToken)
    {
        var uri = new Uri(uriStr);
        if (!this.IsUriAllowed(uri))
        {
            throw new InvalidOperationException("Sending requests to the provided location is not allowed.");
        }

        using var request = new HttpRequestMessage(method, uri) { Content = requestContent };
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(HttpPlugin)));
        using var response = await this._client.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);
    }
    #endregion
}
