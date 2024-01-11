// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;

#pragma warning disable CA2215 // Dispose methods should call base class dispose

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
internal static class HttpClientProvider
{
    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient() => new(NonDisposableHttpClientHandler.Instance, disposeHandler: false);

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(HttpClient? httpClient = null) => httpClient ?? GetHttpClient();

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(IServiceProvider? serviceProvider = null) => GetHttpClient(serviceProvider?.GetService<HttpClient>());

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(HttpClient? httpClient, IServiceProvider serviceProvider) => httpClient ?? GetHttpClient(serviceProvider?.GetService<HttpClient>());

    /// <summary>
    /// Represents a singleton implementation of <see cref="HttpClientHandler"/> that is not disposable.
    /// </summary>
    private sealed class NonDisposableHttpClientHandler : HttpClientHandler
    {
        /// <summary>
        /// Private constructor to prevent direct instantiation of the class.
        /// </summary>
        private NonDisposableHttpClientHandler()
        {
            this.CheckCertificateRevocationList = true;
        }

        /// <summary>
        /// Gets the singleton instance of <see cref="NonDisposableHttpClientHandler"/>.
        /// </summary>
        public static NonDisposableHttpClientHandler Instance { get; } = new();

        /// <summary>
        /// Disposes the underlying resources held by the <see cref="NonDisposableHttpClientHandler"/>.
        /// This implementation does nothing to prevent unintended disposal, as it may affect all references.
        /// </summary>
        /// <param name="disposing">True if called from <see cref="Dispose"/>, false if called from a finalizer.</param>
        protected override void Dispose(bool disposing)
        {
            // Do nothing if called explicitly from Dispose, as it may unintentionally affect all references.
            // The base.Dispose(disposing) is not called to avoid invoking the disposal of HttpClientHandler resources.
            // This implementation assumes that the HttpClientHandler is being used as a singleton and should not be disposed directly.
        }
    }
}
