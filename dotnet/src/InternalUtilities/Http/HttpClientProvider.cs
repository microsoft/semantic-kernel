// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides an HttpClient instance for SK SDK components.
/// </summary>
internal sealed class HttpClientProvider
{
    /// <summary>
    /// The default HttpClientHandler to be used as default by all SK SDK components.
    /// </summary>
    private static HttpClientHandler DefaultHttpClientHandler { get; } = new HttpClientHandler() { CheckCertificateRevocationList = true };

    /// <summary>
    /// Gets an instance of HttpClient with an optional HTTP message handler. If no handler is provided, a default handler is used.
    /// </summary>
    /// <param name="handler">The optional HTTP message handler.</param>
    /// <returns>An instance of HttpClient.</returns>
    internal static HttpClient GetClient(HttpMessageHandler? handler = null)
    {
        return new HttpClient(handler ?? DefaultHttpClientHandler, false); // We should refrain from disposing the underlying SK default HttpClient handler as it would impact other HTTP clients that utilize the same handler.
    }

    /// <summary>
    /// Gets an HttpClient instance with a delegating handler and an optional flag to assign the default handler as inner.
    /// </summary>
    /// <param name="handler">The delegating handler.</param>
    /// <param name="assignDefaultHandlerAsInner">A flag indicating whether to assign the default handler as the inner handler.</param>
    /// <returns>An instance of HttpClient.</returns>
    internal static HttpClient GetClient(DelegatingHandler handler, bool assignDefaultHandlerAsInner = true)
    {
        Verify.NotNull(handler, nameof(handler));

        if (assignDefaultHandlerAsInner)
        {
            handler.InnerHandler = DefaultHttpClientHandler;
        }

        return GetClient(handler);
    }
}
