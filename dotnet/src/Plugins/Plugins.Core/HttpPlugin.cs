// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net;
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
/// Requests are denied by default. Configure <see cref="AllowedOrigins"/>
/// with trusted destinations before sending requests.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedOrigins"/> contains only trusted values.
/// </para>
/// <para>
/// The default HTTP client does not follow redirects to prevent bypassing the allow-list.
/// </para>
/// <para>
/// Allowed hosts are resolved before each request and non-public addresses are rejected unless
/// <see cref="AllowPrivateNetworkAccess"/> is explicitly enabled. The built-in client binds
/// the connection to the validated addresses, and DNS failures are rejected.
/// </para>
/// </remarks>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings",
    Justification = "Semantic Kernel operates on strings")]
public sealed class HttpPlugin
{
    private readonly HttpClient _client;
    private readonly Func<string, CancellationToken, Task<IPAddress[]>>? _dnsResolver;
    private readonly bool _clientSupportsValidatedAddresses;

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
    /// When providing a custom client, configure it with <c>AllowAutoRedirect = false</c> to preserve the origin restrictions.
    /// Hostname requests with a custom client require <see cref="AllowPrivateNetworkAccess"/> because the plugin cannot verify that
    /// the supplied transport connects only to the addresses validated before the request.
    /// </remarks>
    [ActivatorUtilitiesConstructor]
    public HttpPlugin(HttpClient? client = null) : this(
        client,
        dnsResolver: null,
        clientSupportsValidatedAddresses: client is null)
    {
    }

    internal HttpPlugin(
        HttpClient? client,
        Func<string, CancellationToken, Task<IPAddress[]>>? dnsResolver,
        bool clientSupportsValidatedAddresses = false)
    {
        this._client = client ?? HttpClientProvider.GetValidatedNonRedirectingHttpClient();
        this._dnsResolver = dnsResolver;
        this._clientSupportsValidatedAddresses = clientSupportsValidatedAddresses;
    }

    /// <summary>
    /// Gets or sets the allowed combinations of scheme, host, and port for requests.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Defaults to an empty collection. A <see langword="null"/> or empty collection denies all requests.
    /// </para>
    /// <para>
    /// Each origin must be an absolute HTTP or HTTPS URI, such as <c>https://api.example.com:8443</c>,
    /// without credentials, a resource path, a query, or a fragment.
    /// An omitted port means 80 for HTTP or 443 for HTTPS.
    /// </para>
    /// <para>
    /// Scheme and host comparisons ignore case. All resource paths on a matching origin are permitted.
    /// Private-network restrictions still apply.
    /// </para>
    /// </remarks>
    /// <exception cref="ArgumentException">An entry is not a valid HTTP or HTTPS origin.</exception>
    public IEnumerable<Uri>? AllowedOrigins
    {
        get => this._allowedOrigins;
        set => this._allowedOrigins = HttpOriginAllowList.Create(value, nameof(this.AllowedOrigins));
    }

    /// <summary>
    /// Gets or sets whether allowed hosts may resolve to private, loopback, link-local,
    /// or other non-public addresses. Defaults to <see langword="false"/>.
    /// </summary>
    /// <remarks>
    /// Enable only for trusted internal endpoints. Origin restrictions still apply and
    /// the default HTTP client still rejects redirects.
    /// </remarks>
    public bool AllowPrivateNetworkAccess { get; set; }

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
    private IReadOnlyList<Uri>? _allowedOrigins = [];

    /// <summary>
    /// Checks whether the request destination matches an allowed origin.
    /// </summary>
    /// <param name="uri">The request URI to check.</param>
    /// <returns><see langword="true"/> if the destination is permitted; otherwise, <see langword="false"/>.</returns>
    private bool IsUriAllowed(Uri uri)
    {
        Verify.NotNull(uri);

        return HttpOriginAllowList.Contains(this._allowedOrigins, uri);
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

        IPAddress[] validatedAddresses = [];
        if (!this.AllowPrivateNetworkAccess)
        {
            validatedAddresses = await PublicNetworkAddressValidator.ValidateAsync(
                uri, cancellationToken,
                dnsResolver: this._dnsResolver,
                configurationHint: $"To allow trusted internal endpoints, set {nameof(this.AllowPrivateNetworkAccess)} = true.").ConfigureAwait(false);
        }

        using var request = new HttpRequestMessage(method, uri) { Content = requestContent };
#if NET
        if (validatedAddresses.Length > 0)
        {
            if (!this._clientSupportsValidatedAddresses)
            {
                throw new InvalidOperationException(
                    $"Requests to hostnames require the built-in HTTP client when {nameof(this.AllowPrivateNetworkAccess)} is false. " +
                    $"Use the built-in client, or configure the supplied client transport and explicitly set {nameof(this.AllowPrivateNetworkAccess)} = true.");
            }

            request.Options.Set(HttpClientProvider.ValidatedAddressesKey, validatedAddresses);
        }
#else
        if (validatedAddresses.Length > 0)
        {
            throw new PlatformNotSupportedException(
                $"Requests to hostnames with {nameof(this.AllowPrivateNetworkAccess)} set to false require a .NET target that supports binding HTTP connections to validated addresses.");
        }
#endif
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(HttpPlugin)));
        using var response = await this._client.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);
    }
    #endregion
}
