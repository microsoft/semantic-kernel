// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
#if NET
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;
#endif
using Microsoft.Extensions.DependencyInjection;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable CA2215 // Dispose methods should call base class dispose

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
[ExcludeFromCodeCoverage]
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
    private sealed class NonDisposableHttpClientHandler : DelegatingHandler
    {
        /// <summary>
        /// Private constructor to prevent direct instantiation of the class.
        /// </summary>
        private NonDisposableHttpClientHandler() : base(CreateHandler())
        {
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
            // This implementation assumes that the HttpMessageHandler is being used as a singleton and should not be disposed directly.
        }

#if NET
        private static SocketsHttpHandler CreateHandler()
        {
            return new SocketsHttpHandler()
            {
                // Limit the lifetime of connections to better respect any DNS changes
                PooledConnectionLifetime = TimeSpan.FromMinutes(2),

                // Check cert revocation
                SslOptions = new SslClientAuthenticationOptions()
                {
                    CertificateRevocationCheckMode = X509RevocationMode.Online,
                },
            };
        }
#elif NETSTANDARD2_0
        private static HttpClientHandler CreateHandler()
        {
            var handler = new HttpClientHandler();
            try
            {
                handler.CheckCertificateRevocationList = true;
            }
            catch (PlatformNotSupportedException) { } // not supported on older frameworks
            return handler;
        }
#elif NET462 || NET472
        private static HttpClientHandler CreateHandler()
            => new();
#endif
    }
}
