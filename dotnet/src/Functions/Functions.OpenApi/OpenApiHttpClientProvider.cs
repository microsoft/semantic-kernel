// Copyright (c) Microsoft. All rights reserved.

#if NET
using System.Net;
#endif
using System.Net.Http;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Creates the built-in OpenAPI HTTP client and binds validated DNS addresses to its connections.
/// </summary>
internal static class OpenApiHttpClientProvider
{
#if NET
    internal static readonly HttpRequestOptionsKey<IPAddress[]> ValidatedAddressesKey = HttpClientProvider.ValidatedAddressesKey;
#endif

    /// <summary>
    /// Creates a non-redirecting client backed by shared, isolated validated and unchecked connection pools.
    /// </summary>
    public static HttpClient CreateHttpClient() => HttpClientProvider.GetValidatedNonRedirectingHttpClient();
}
